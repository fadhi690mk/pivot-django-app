from django.http import HttpResponse
from django.template import Template, Context
from django.template.loader import render_to_string
from django.conf import settings as django_settings
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from accounts.permissions import HasHubPermission
from .models import Invoice
from .serializers import InvoiceSerializer, InvoiceCreateSerializer, InvoiceUpdateSerializer


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated, HasHubPermission])
def invoice_list_create(request):
    invoice_list_create.required_permissions = {"GET": "invoices.view", "POST": "invoices.create"}
    if request.method == "POST":
        serializer = InvoiceCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        inv = serializer.save()
        from audit.utils import log_audit
        log_audit(request, "create", "invoices", f"Invoice {inv.invoice_number}", str(inv.id), "Invoice created")
        return Response(InvoiceSerializer(inv).data, status=status.HTTP_201_CREATED)
    qs = Invoice.objects.select_related("lead").prefetch_related("items").all().order_by("-created_at")
    for param, field in [("type", "type"), ("status", "status")]:
        val = request.query_params.get(param)
        if val:
            qs = qs.filter(**{field: val})
    from rest_framework.pagination import PageNumberPagination
    paginator = PageNumberPagination()
    paginator.page_size = 20
    page = paginator.paginate_queryset(qs, request)
    return paginator.get_paginated_response(InvoiceSerializer(page, many=True).data)


@api_view(["GET", "PATCH", "DELETE"])
@permission_classes([IsAuthenticated, HasHubPermission])
def invoice_detail(request, pk):
    try:
        inv = Invoice.objects.select_related("lead").prefetch_related("items").get(pk=pk)
    except Invoice.DoesNotExist:
        return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
    if request.method == "GET":
        return Response(InvoiceSerializer(inv).data)
    if request.method == "PATCH":
        serializer = InvoiceUpdateSerializer(inv, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        from audit.utils import log_audit
        log_audit(request, "update", "invoices", f"Invoice {inv.invoice_number}", str(inv.id), "Invoice updated")
        return Response(InvoiceSerializer(Invoice.objects.select_related("lead").prefetch_related("items").get(pk=pk)).data)
    if request.method == "DELETE":
        num = inv.invoice_number
        inv.delete()
        from audit.utils import log_audit
        log_audit(request, "delete", "invoices", f"Invoice {num}", str(pk), "Invoice deleted")
        return Response(status=status.HTTP_204_NO_CONTENT)
    return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)


invoice_detail.required_permissions = {"GET": "invoices.view", "PATCH": "invoices.edit", "DELETE": "invoices.delete"}


@api_view(["PATCH"])
@permission_classes([IsAuthenticated, HasHubPermission])
def invoice_status(request, pk):
    request.required_permission = "invoices.edit"
    try:
        inv = Invoice.objects.get(pk=pk)
    except Invoice.DoesNotExist:
        return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
    new_status = request.data.get("status")
    if not new_status:
        return Response({"status": ["Required."]}, status=status.HTTP_400_BAD_REQUEST)
    inv.status = new_status
    if new_status == "paid" and not inv.paid_date:
        from datetime import date
        inv.paid_date = date.today()
    inv.save()
    return Response(InvoiceSerializer(Invoice.objects.select_related("lead").prefetch_related("items").get(pk=pk)).data)


def _invoice_context(inv):
    """Build context for invoice email/print template."""
    company = {
        "name": getattr(django_settings, "COMPANY_NAME", "Pivot Travels & Tourism"),
        "tagline": getattr(django_settings, "COMPANY_TAGLINE", "UAE Business Setup & Visa Services"),
        "email": getattr(django_settings, "COMPANY_EMAIL", ""),
        "phone": getattr(django_settings, "COMPANY_PHONE", ""),
        "address": getattr(django_settings, "COMPANY_ADDRESS", "Dubai, United Arab Emirates"),
        "website": getattr(django_settings, "COMPANY_WEBSITE", ""),
    }
    items = list(inv.items.order_by("sort_order"))
    return {"invoice": inv, "items": items, "company": company}


@api_view(["GET"])
@permission_classes([IsAuthenticated, HasHubPermission])
def invoice_download(request, pk):
    request.required_permission = "invoices.view"
    try:
        inv = Invoice.objects.select_related("lead").prefetch_related("items").get(pk=pk)
    except Invoice.DoesNotExist:
        return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
    context = _invoice_context(inv)
    context["for_download"] = True
    html = render_to_string("invoices/email_invoice.html", context)
    return HttpResponse(html, content_type="text/html; charset=utf-8")


@api_view(["POST"])
@permission_classes([IsAuthenticated, HasHubPermission])
def invoice_send_email(request, pk):
    request.required_permission = "invoices.view"
    try:
        inv = Invoice.objects.select_related("lead").prefetch_related("items").get(pk=pk)
    except Invoice.DoesNotExist:
        return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
    to_email = (request.data.get("to_email") or "").strip() or inv.client_email
    if not to_email:
        return Response({"detail": "No email address."}, status=status.HTTP_400_BAD_REQUEST)
    context = _invoice_context(inv)
    context["for_download"] = False
    html_content = render_to_string("invoices/email_invoice.html", context)
    company = context["company"]
    text_body = (
        f"Hello {inv.client_name},\n\n"
        f"Please find your {inv.get_type_display().lower()} {inv.invoice_number} below.\n\n"
        f"Total: {inv.total} SAR\n\n"
        f"Best regards,\n{company['name']}"
    )
    subject = f"{inv.get_type_display()}: {inv.invoice_number}"
    from_email = getattr(django_settings, "DEFAULT_FROM_EMAIL", "noreply@example.com")
    try:
        from core.tasks import queue_send_mail
        queue_send_mail(
            to_email=to_email,
            subject=subject,
            body_text=text_body,
            body_html=html_content,
            from_email=from_email,
        )
    except Exception as e:
        return Response({"detail": "Mail queue unavailable: %s" % e}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
    return Response({"detail": "Email queued. It will be sent within the next 13 seconds."})
