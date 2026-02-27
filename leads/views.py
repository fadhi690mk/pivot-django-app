from django.db import models
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination

from accounts.permissions import HasHubPermission
from .models import Lead, LeadNote
from .serializers import LeadListSerializer, LeadDetailSerializer, LeadCreatePublicSerializer, LeadNoteSerializer
from .id_generator import generate_lead_id
from audit.utils import log_audit
from awamer.firebase_fcm import send_lead_notification


class LeadPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100


@api_view(["POST"])
@permission_classes([AllowAny])
def public_lead_create(request):
    serializer = LeadCreatePublicSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    lead = serializer.save()
    try:
        send_lead_notification(lead)
    except Exception:
        pass
    return Response(
        {"id": lead.id, "message": "Lead created successfully."},
        status=status.HTTP_201_CREATED,
    )


@api_view(["PATCH"])
@permission_classes([AllowAny])
def public_lead_update(request, pk):
    """Update a lead (calculator flow: add service/jurisdiction/estimated_value)."""
    try:
        lead = Lead.objects.get(pk=pk)
    except Lead.DoesNotExist:
        return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
    data = request.data
    if isinstance(data.get("service_id"), str) and data["service_id"]:
        from cms.models import Service
        try:
            lead.service = Service.objects.get(pk=data["service_id"])
        except Service.DoesNotExist:
            pass
    for field in ("service_interest", "sub_service", "jurisdiction", "estimated_value"):
        if field in data and data[field] is not None:
            if field == "estimated_value":
                lead.estimated_value = data[field]
            else:
                setattr(lead, field, data[field])
    lead.save()
    return Response({"id": lead.id, "message": "Lead updated."})


@api_view(["POST"])
@permission_classes([IsAuthenticated, HasHubPermission])
def lead_bulk_create(request):
    lead_bulk_create.required_permission = "leads.create"
    items = request.data.get("leads")
    if not isinstance(items, list):
        return Response({"detail": "Expected a list of leads in 'leads'."}, status=status.HTTP_400_BAD_REQUEST)
    created = []
    errors = []
    for i, item in enumerate(items):
        if not isinstance(item, dict):
            errors.append({"index": i, "error": "Invalid item"})
            continue
        serializer = LeadCreatePublicSerializer(data=item)
        if not serializer.is_valid():
            errors.append({"index": i, "error": serializer.errors})
            continue
        lead = serializer.save()
        log_audit(request, "create", "leads", f"Lead {lead.id}", lead.id, lead.name)
        created.append({"id": lead.id, "name": lead.name, "email": lead.email})
    return Response({"created": len(created), "leads": created, "errors": errors if errors else None}, status=status.HTTP_201_CREATED)


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated, HasHubPermission])
def lead_list(request):
    if request.method == "POST":
        lead_list.required_permission = "leads.create"
        serializer = LeadCreatePublicSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        lead = serializer.save()
        log_audit(request, "create", "leads", f"Lead {lead.id}", lead.id, lead.name)
        return Response(
            {"id": lead.id, "message": "Lead created successfully."},
            status=status.HTTP_201_CREATED,
        )
    lead_list.required_permission = "leads.view"
    qs = Lead.objects.all().select_related("assigned_to", "service").prefetch_related("tags", "notes")
    search = request.query_params.get("search", "").strip()
    if search:
        qs = qs.filter(
            models.Q(name__icontains=search)
            | models.Q(email__icontains=search)
            | models.Q(company__icontains=search)
            | models.Q(service_interest__icontains=search)
            | models.Q(id__icontains=search)
        )
    for param, field in [("status", "status"), ("source", "source"), ("priority", "priority")]:
        val = request.query_params.get(param)
        if val:
            qs = qs.filter(**{field: val})
    assigned = request.query_params.get("assigned_to")
    if assigned:
        qs = qs.filter(assigned_to_id=assigned)
    service_id = request.query_params.get("service") or request.query_params.get("service_id")
    if service_id:
        qs = qs.filter(service_id=service_id)
    ordering = request.query_params.get("ordering", "-created_at")
    qs = qs.order_by(ordering)
    paginator = LeadPagination()
    page = paginator.paginate_queryset(qs, request)
    serializer = LeadListSerializer(page, many=True)
    return paginator.get_paginated_response(serializer.data)


@api_view(["GET", "PATCH"])
@permission_classes([IsAuthenticated, HasHubPermission])
def lead_detail(request, pk):
    try:
        lead = Lead.objects.select_related("assigned_to", "service").prefetch_related("tags", "notes", "chat_messages").get(pk=pk)
    except Lead.DoesNotExist:
        return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
    if request.method == "PATCH":
        allowed = [
            "status", "priority", "assigned_to", "estimated_value", "last_contacted_at",
            "name", "email", "phone", "company",
        ]
        for field in allowed:
            if field in request.data:
                setattr(lead, field, request.data[field])
        lead.save()
        log_audit(request, "update", "leads", f"Lead {lead.id}", str(lead.id), lead.name)
        lead = Lead.objects.select_related("assigned_to", "service").prefetch_related("tags", "notes", "chat_messages").get(pk=pk)
    return Response(LeadDetailSerializer(lead).data)


lead_detail.required_permissions = {"GET": "leads.view", "PATCH": "leads.edit"}


@api_view(["POST"])
@permission_classes([IsAuthenticated, HasHubPermission])
def lead_add_note(request, pk):
    request.required_permission = "leads.edit"
    try:
        lead = Lead.objects.get(pk=pk)
    except Lead.DoesNotExist:
        return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
    text = request.data.get("text")
    if not text:
        return Response({"text": ["This field is required."]}, status=status.HTTP_400_BAD_REQUEST)
    note = LeadNote.objects.create(lead=lead, text=text, author=request.user.name)
    log_audit(request, "add_note", "leads", f"Lead {lead.id}", str(lead.id), f"Note added to lead {lead.name}")
    return Response(LeadNoteSerializer(note).data, status=status.HTTP_201_CREATED)


@api_view(["POST"])
@permission_classes([IsAuthenticated, HasHubPermission])
def lead_assign(request, pk):
    request.required_permission = "leads.assign"
    try:
        lead = Lead.objects.get(pk=pk)
    except Lead.DoesNotExist:
        return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
    assigned_to_id = request.data.get("assigned_to")
    from accounts.models import HubUser
    if assigned_to_id:
        try:
            user = HubUser.objects.get(pk=assigned_to_id, is_deleted=False)
        except HubUser.DoesNotExist:
            return Response({"assigned_to": ["User not found."]}, status=status.HTTP_400_BAD_REQUEST)
        lead.assigned_to = user
    else:
        lead.assigned_to = None
    lead.save()
    log_audit(request, "assign", "leads", f"Lead {lead.id}", str(lead.id), f"Lead {lead.name} assigned")
    return Response(LeadDetailSerializer(Lead.objects.get(pk=pk)).data)


