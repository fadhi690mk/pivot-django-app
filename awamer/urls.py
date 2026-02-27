from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/auth/", include("accounts.urls")),
    path("api/leads/", include("leads.urls")),
    path("api/public/leads/", include("leads.urls_public")),
    path("api/invoices/", include("invoices.urls")),
    path("api/cms/", include("cms.urls_public")),
    path("api/config/", include("config_app.urls")),
    path("api/hub/audit/", include("audit.urls")),
    path("api/hub/cms/", include("cms.urls_hub")),
    path("api/hub/config/", include("config_app.urls_hub")),
    path("api/ai/", include("ai_sales.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
