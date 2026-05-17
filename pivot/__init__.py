# Load Celery app when Django starts (for workers and beat)
from .celery import app as celery_app

__all__ = ("celery_app",)
