"""
Audit logging helper. Call from hub views that perform create/update/delete.
"""


def get_client_ip(request):
    if not request:
        return None
    xff = request.META.get("HTTP_X_FORWARDED_FOR")
    if xff:
        return xff.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


def log_audit(request, action, module, target, target_id=None, details=""):
    """
    Create an AuditEntry. Use action: create, update, delete, view, login, etc.
    module: leads, invoices, cms, config, auth, roles, etc.
    target: human-readable (e.g. "Lead", "Invoice INV-001")
    """
    from .models import AuditEntry

    user = getattr(request, "user", None)
    user_display = ""
    user_id = None
    if user and getattr(user, "is_authenticated", False) and user.is_authenticated:
        user_display = getattr(user, "name", None) or getattr(user, "email", "") or str(user)
        user_id = getattr(user, "pk", None)
    else:
        user_display = "Anonymous"

    ip = get_client_ip(request)
    AuditEntry.objects.create(
        user_id=user_id,
        user_display=user_display[:255],
        action=action[:20],
        module=module[:50],
        target=str(target)[:255],
        target_id=str(target_id)[:100] if target_id else None,
        details=(details or "")[:2000],
        ip_address=ip,
    )
