"""
Summarize last N messages into lead.chat_summary for token reduction.
Uses Groq LLM; keeps under ~150 words; structured format.
"""
import logging
from django.conf import settings

logger = logging.getLogger(__name__)

SUMMARY_PROMPT = """Summarize this customer chat into a short memory for future replies. Use this format:

Customer Intent:
- (bullet points: what they want, budget/timeline if mentioned)

Key Topics:
- (bullet points: services/topics discussed)

Keep under 150 words. No fluff. Only facts from the chat.

Chat:
---
{chat_text}
---"""


def update_lead_summary(lead) -> bool:
    """
    Take last 6–10 messages from the lead's session, summarize with Groq, store in lead.chat_summary.
    Returns True if summary was updated.
    """
    if not lead or not getattr(lead, "chat_session", None):
        return False
    session = lead.chat_session
    messages = list(
        session.messages.filter(role__in=("user", "assistant"))
        .order_by("-created_at")[:10]
    )
    messages.reverse()
    if not messages:
        return False
    chat_lines = []
    for m in messages:
        role = "Customer" if m.role == "user" else "Assistant"
        chat_lines.append(f"{role}: {m.content}")
    chat_text = "\n".join(chat_lines)

    api_key = getattr(settings, "GROQ_API_KEY", None) or ""
    if not api_key.strip():
        logger.warning("GROQ_API_KEY not set; skipping summary")
        return False
    try:
        from groq import Groq
        client = Groq(api_key=api_key.strip())
        prompt = SUMMARY_PROMPT.format(chat_text=chat_text[:4000])
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=300,
            temperature=0.3,
        )
        summary = (response.choices[0].message.content or "").strip()
        if not summary:
            return False
        lead.chat_summary = summary[:2000]
        lead.save(update_fields=["chat_summary"])
        return True
    except Exception as e:
        logger.warning("Summary update failed: %s", e)
        return False
