"""
Celery tasks. send_queued_mail enforces a 13-second gap between sends via Redis.
"""
import logging
import time
from celery import shared_task
from django.core.mail import EmailMultiAlternatives
from django.conf import settings

logger = logging.getLogger(__name__)

# Enforce 13 seconds between each mail send (via Redis throttle; use single worker for this queue if possible)
MAIL_GAP_SECONDS = 13
REDIS_KEY_LAST_SEND = "celery:mail_queue:last_send"
REDIS_LOCK_KEY = "celery:mail_queue:lock"
REDIS_LOCK_TIMEOUT = 60


def _get_redis():
    import redis
    return redis.Redis.from_url(settings.CELERY_BROKER_URL)


@shared_task(
    name="core.tasks.send_queued_mail",
    bind=True,
    max_retries=3,
)
def send_queued_mail(self, to_email: str, subject: str, body_text: str, body_html: str = None, from_email: str = None):
    """
    Send one email. Queued by queue_send_mail(). Throttled so there is at least 13s between sends (via Redis).
    """
    from redis.lock import Lock
    from_email = from_email or getattr(settings, "DEFAULT_FROM_EMAIL", "noreply@example.com")
    to_list = [e.strip() for e in (to_email or "").split(",") if e.strip()]
    if not to_list:
        logger.warning("send_queued_mail: no recipient")
        return
    try:
        r = _get_redis()
        with Lock(r, REDIS_LOCK_KEY, timeout=REDIS_LOCK_TIMEOUT):
            last_send = r.get(REDIS_KEY_LAST_SEND)
            last_ts = float(last_send) if last_send else 0
            now = time.time()
            sleep_secs = max(0, MAIL_GAP_SECONDS - (now - last_ts))
            if sleep_secs > 0:
                time.sleep(sleep_secs)
            msg = EmailMultiAlternatives(subject, body_text, from_email, to_list)
            if body_html:
                msg.attach_alternative(body_html, "text/html")
            msg.send(fail_silently=False)
            r.set(REDIS_KEY_LAST_SEND, time.time())
        logger.info("Queued email sent to %s: %s", to_list[0], subject[:50])
    except Exception as e:
        logger.warning("send_queued_mail failed: %s", e)
        raise self.retry(exc=e, countdown=60)


def queue_send_mail(to_email: str, subject: str, body_text: str, body_html: str = None, from_email: str = None):
    """
    Queue an email to be sent via Celery. Each send respects a 13-second gap.
    """
    send_queued_mail.delay(
        to_email=to_email,
        subject=subject,
        body_text=body_text,
        body_html=body_html,
        from_email=from_email,
    )
