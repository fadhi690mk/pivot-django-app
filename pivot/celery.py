"""
Celery app for pivot project. Used for mail queue (13s gap between emails).
"""
import os
from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "pivot.settings")

app = Celery("pivot")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()


# Handle tasks enqueued as 'shop.tasks.send_email_task' (e.g. from another service or old code)
@app.task(
    name="shop.tasks.send_email_task",
    bind=True,
    max_retries=3,
)
def send_email_task(
    self,
    to_address=None,
    subject=None,
    content=None,
    template_name=None,
    context=None,
    bcc_address=None,
    attachments=None,
    temp_attachments=None,
):
    from core.tasks import queue_send_mail
    queue_send_mail(
        to_email=to_address or "",
        subject=subject or "",
        body_text=content or "",
        body_html=None,
    )


@app.task(bind=True)
def debug_task(self):
    print(f"Request: {self.request!r}")
