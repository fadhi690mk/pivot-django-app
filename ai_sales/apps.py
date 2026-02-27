from django.apps import AppConfig


class AiSalesConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "ai_sales"
    verbose_name = "AI Sales (Chat)"

    def ready(self):
        import ai_sales.signals  # noqa: F401
