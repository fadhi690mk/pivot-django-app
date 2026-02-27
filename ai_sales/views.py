"""
AI chat: SSE stream endpoint and lead-attach on public lead create.
"""
import json
import logging
import re
import time
from django.http import StreamingHttpResponse, HttpResponse
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET
from django.core.cache import cache

from ai_sales.services.orchestrator import stream_chat_response

logger = logging.getLogger(__name__)
SESSION_ID_PATTERN = re.compile(r"^[a-zA-Z0-9_\-]{1,255}$")
RATE_LIMIT_KEY = "ai_chat_stream:%s"
RATE_LIMIT_WINDOW = 60
RATE_LIMIT_MAX = 30


def _rate_limit_key(request):
    """Rate limit by IP."""
    xff = request.META.get("HTTP_X_FORWARDED_FOR")
    if xff:
        return xff.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR", "")


@require_GET
@never_cache
def chat_stream(request):
    """
    GET /api/ai/chat/stream/?session_id=xxx&message=xxx
    Returns text/event-stream. Rate limited by IP.
    """
    ip = _rate_limit_key(request)
    cache_key = RATE_LIMIT_KEY % ip
    now = time.time()
    window_start = cache.get(cache_key + ":start", now)
    if now - window_start > RATE_LIMIT_WINDOW:
        cache.set(cache_key + ":start", now, RATE_LIMIT_WINDOW * 2)
        cache.set(cache_key + ":count", 1, RATE_LIMIT_WINDOW * 2)
    else:
        count = cache.get(cache_key + ":count", 0) + 1
        cache.set(cache_key + ":count", count, RATE_LIMIT_WINDOW * 2)
        if count > RATE_LIMIT_MAX:
            return HttpResponse(
                json.dumps({"error": "Too many requests"}),
                status=429,
                content_type="application/json",
            )

    session_id = (request.GET.get("session_id") or "").strip()
    message = (request.GET.get("message") or "").strip()

    if not SESSION_ID_PATTERN.match(session_id):
        return HttpResponse(
            json.dumps({"error": "Invalid session_id"}),
            status=400,
            content_type="application/json",
        )

    def event_stream():
        try:
            gen = stream_chat_response(session_id, message)
            first = next(gen)
            if isinstance(first, dict):
                yield f"data: {json.dumps(first)}\n\n"
                if first.get("require_lead") or first.get("error"):
                    yield "data: [DONE]\n\n"
                    return
                if first.get("safe_fallback"):
                    yield f"data: {json.dumps({'token': first['safe_fallback']})}\n\n"
                    yield "data: [DONE]\n\n"
                    return
            for chunk in gen:
                if isinstance(chunk, dict):
                    yield f"data: {json.dumps(chunk)}\n\n"
                else:
                    yield f"data: {json.dumps({'token': chunk})}\n\n"
            yield "data: [DONE]\n\n"
        except Exception as e:
            logger.exception("chat_stream: %s", e)
            yield f"data: {json.dumps({'error': 'Server error'})}\n\n"
            yield "data: [DONE]\n\n"

    response = StreamingHttpResponse(
        event_stream(),
        content_type="text/event-stream",
    )
    response["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response["X-Accel-Buffering"] = "no"
    return response
