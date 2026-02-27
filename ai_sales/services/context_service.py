"""
Simple chat context from Django models. No vector DB or embeddings.
Fetches published services, blog, news, FAQ and formats as text for the LLM prompt.
"""
import logging
from django.db.models import Q

logger = logging.getLogger(__name__)

# Max chars per section to keep prompt size reasonable
MAX_SERVICES = 15
MAX_BLOG = 5
MAX_NEWS = 5
MAX_FAQ = 10
MAX_TEXT_LEN = 300  # per item description/excerpt


def get_simple_context(user_message: str) -> str:
    """
    Build context string from published CMS content.
    Optionally filters by keyword (user message words) for slight relevance.
    """
    parts = []
    try:
        from cms.models import Service, SubService, BlogPost, NewsItem, FAQ
    except ImportError:
        return "(Content not available.)"

    msg_words = [w.strip().lower() for w in (user_message or "").split() if len(w.strip()) > 2]
    base_filter = Q(status="published", is_deleted=False)

    # --- Services ---
    try:
        qs = Service.objects.filter(base_filter).order_by("sort_order", "title")[:MAX_SERVICES]
        if msg_words:
            kw_filter = Q()
            for w in msg_words[:5]:
                kw_filter |= Q(title__icontains=w) | Q(description__icontains=w) | Q(tagline__icontains=w)
            qs = Service.objects.filter(base_filter).filter(kw_filter).order_by("sort_order", "title")[:MAX_SERVICES]
        if qs.exists():
            lines = ["Services:"]
            for s in qs:
                desc = (s.description or s.tagline or "")[:MAX_TEXT_LEN]
                lines.append(f"  - {s.title}: {desc}")
            parts.append("\n".join(lines))
    except Exception as e:
        logger.warning("Simple context services: %s", e)

    # --- Sub-services ---
    try:
        qs = SubService.objects.filter(base_filter).select_related("parent_service").order_by("parent_service__sort_order", "sort_order")[:MAX_SERVICES]
        if msg_words:
            kw_filter = Q()
            for w in msg_words[:5]:
                kw_filter |= Q(title__icontains=w) | Q(description__icontains=w)
            qs = SubService.objects.filter(base_filter).filter(kw_filter).select_related("parent_service").order_by("parent_service__sort_order", "sort_order")[:MAX_SERVICES]
        if qs.exists():
            lines = ["Sub-services:"]
            for s in qs:
                parent = getattr(s.parent_service, "title", "") or "Service"
                desc = (s.description or s.tagline or "")[:MAX_TEXT_LEN]
                lines.append(f"  - {parent} / {s.title}: {desc}")
            parts.append("\n".join(lines))
    except Exception as e:
        logger.warning("Simple context subservices: %s", e)

    # --- Blog ---
    try:
        qs = BlogPost.objects.filter(base_filter).order_by("-published_at")[:MAX_BLOG]
        if msg_words:
            kw_filter = Q()
            for w in msg_words[:5]:
                kw_filter |= Q(title__icontains=w) | Q(excerpt__icontains=w)
            qs = BlogPost.objects.filter(base_filter).filter(kw_filter).order_by("-published_at")[:MAX_BLOG]
        if qs.exists():
            lines = ["Blog:"]
            for b in qs:
                ex = (b.excerpt or "")[:MAX_TEXT_LEN]
                lines.append(f"  - {b.title}: {ex}")
            parts.append("\n".join(lines))
    except Exception as e:
        logger.warning("Simple context blog: %s", e)

    # --- News ---
    try:
        qs = NewsItem.objects.filter(base_filter).order_by("-published_at")[:MAX_NEWS]
        if msg_words:
            kw_filter = Q()
            for w in msg_words[:5]:
                kw_filter |= Q(title__icontains=w) | Q(excerpt__icontains=w)
            qs = NewsItem.objects.filter(base_filter).filter(kw_filter).order_by("-published_at")[:MAX_NEWS]
        if qs.exists():
            lines = ["News:"]
            for n in qs:
                ex = (n.excerpt or "")[:MAX_TEXT_LEN]
                lines.append(f"  - {n.title}: {ex}")
            parts.append("\n".join(lines))
    except Exception as e:
        logger.warning("Simple context news: %s", e)

    # --- FAQ ---
    try:
        qs = FAQ.objects.filter(base_filter).order_by("category", "sort_order")[:MAX_FAQ]
        if msg_words:
            kw_filter = Q()
            for w in msg_words[:5]:
                kw_filter |= Q(question__icontains=w) | Q(answer__icontains=w)
            qs = FAQ.objects.filter(base_filter).filter(kw_filter).order_by("category", "sort_order")[:MAX_FAQ]
        if qs.exists():
            lines = ["FAQ:"]
            for f in qs:
                lines.append(f"  Q: {f.question[:150]}")
                lines.append(f"  A: {(f.answer or '')[:MAX_TEXT_LEN]}")
            parts.append("\n".join(lines))
    except Exception as e:
        logger.warning("Simple context FAQ: %s", e)

    if not parts:
        return "(No published content available. You can still answer generally about business setup and visa services in UAE.)"
    return "\n\n".join(parts)
