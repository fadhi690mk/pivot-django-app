import uuid
from django.db import models


class AuditEntry(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        "accounts.HubUser", null=True, on_delete=models.SET_NULL, related_name="audit_entries"
    )
    user_display = models.CharField(max_length=255)
    action = models.CharField(max_length=20)
    module = models.CharField(max_length=50)
    target = models.CharField(max_length=255)
    target_id = models.CharField(max_length=100, blank=True, null=True)
    details = models.TextField()
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "audit_entry"
        ordering = ["-timestamp"]
