from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from accounts.permissions import HasHubPermission
from .models import AuditEntry


@api_view(["GET"])
@permission_classes([IsAuthenticated, HasHubPermission])
def audit_list(request):
    qs = AuditEntry.objects.all().order_by("-timestamp")
    user_id = request.query_params.get("user_id", "").strip()
    if user_id:
        qs = qs.filter(user_id=user_id)
    from rest_framework.pagination import PageNumberPagination
    paginator = PageNumberPagination()
    paginator.page_size = 20
    page = paginator.paginate_queryset(qs, request)
    data = [
        {
            "id": str(e.id),
            "user_display": e.user_display,
            "action": e.action,
            "module": e.module,
            "target": e.target,
            "target_id": e.target_id,
            "details": e.details,
            "ip_address": str(e.ip_address) if e.ip_address else None,
            "timestamp": e.timestamp.isoformat(),
        }
        for e in page
    ]
    return paginator.get_paginated_response(data)


audit_list.required_permission = "audit.view"


@api_view(["GET"])
@permission_classes([IsAuthenticated, HasHubPermission])
def audit_users(request):
    """Return distinct users that have audit entries (for filter dropdown)."""
    from django.db.models import Count
    qs = (
        AuditEntry.objects.filter(user_id__isnull=False)
        .values("user_id", "user_display")
        .annotate(count=Count("id"))
        .order_by("user_display")
    )
    seen = set()
    out = []
    for e in qs:
        uid = e["user_id"]
        if uid not in seen:
            seen.add(uid)
            out.append({"id": str(uid), "name": e["user_display"]})
    return Response(out)


audit_users.required_permission = "audit.view"
