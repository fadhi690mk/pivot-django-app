from django.contrib import admin
from .models import AuditEntry


@admin.register(AuditEntry)
class AuditEntryAdmin(admin.ModelAdmin):
    list_display = ["timestamp", "user_display", "action", "module", "target"]
    readonly_fields = ["id", "user", "user_display", "action", "module", "target", "target_id", "details", "ip_address", "timestamp"]
