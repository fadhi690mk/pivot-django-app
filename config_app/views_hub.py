from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from accounts.permissions import HasHubPermission
from .models import BusinessActivity, Jurisdiction, CalculatorService, SearchSuggestion


def _activity_payload(a):
    return {"id": a.id, "label": a.label, "icon": a.icon or "", "status": a.status, "sort_order": a.sort_order}


def _jurisdiction_payload(j):
    return {
        "id": j.id, "label": j.label, "description": j.description or "",
        "base_price": j.base_price, "basePrice": j.base_price, "status": j.status,
    }


def _calc_service_payload(s):
    out = {"id": str(s.id), "label": s.label, "price": s.price, "per": s.per, "status": s.status, "sort_order": s.sort_order}
    if s.service_id:
        out["service_id"] = str(s.service.id)
        out["service_slug"] = s.service.slug
        out["service_title"] = s.service.title
    return out


@api_view(["GET"])
@permission_classes([IsAuthenticated, HasHubPermission])
def hub_calculator_config(request):
    hub_calculator_config.required_permission = "config.calculator"
    activities = BusinessActivity.objects.all().order_by("sort_order", "id")
    jurisdictions = Jurisdiction.objects.all().order_by("id")
    services = CalculatorService.objects.all().select_related("service").order_by("sort_order", "label")
    return Response({
        "activities": [_activity_payload(a) for a in activities],
        "jurisdictions": [_jurisdiction_payload(j) for j in jurisdictions],
        "additional_services": [_calc_service_payload(s) for s in services],
    })


# ---------- Activities ----------
@api_view(["POST"])
@permission_classes([IsAuthenticated, HasHubPermission])
def hub_calculator_activity_list_create(request):
    hub_calculator_activity_list_create.required_permission = "config.calculator"
    data = request.data
    id_val = (data.get("id") or "").strip() or None
    label = (data.get("label") or "").strip()
    if not label:
        return Response({"label": ["This field is required."]}, status=status.HTTP_400_BAD_REQUEST)
    if not id_val:
        id_val = label.lower().replace(" ", "_")[:50]
    if BusinessActivity.objects.filter(id=id_val).exists():
        return Response({"id": ["Activity with this id already exists."]}, status=status.HTTP_400_BAD_REQUEST)
    activity = BusinessActivity.objects.create(
        id=id_val,
        label=label,
        icon=(data.get("icon") or "").strip() or None,
        status=data.get("status") or "published",
        sort_order=data.get("sort_order") or 0,
    )
    return Response(_activity_payload(activity), status=status.HTTP_201_CREATED)


@api_view(["PATCH", "DELETE"])
@permission_classes([IsAuthenticated, HasHubPermission])
def hub_calculator_activity_detail(request, pk):
    hub_calculator_activity_detail.required_permission = "config.calculator"
    try:
        activity = BusinessActivity.objects.get(pk=pk)
    except BusinessActivity.DoesNotExist:
        return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
    if request.method == "DELETE":
        activity.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    data = request.data
    if "label" in data:
        activity.label = (data["label"] or "").strip() or activity.label
    if "icon" in data:
        activity.icon = (data["icon"] or "").strip() or None
    if "status" in data:
        activity.status = data["status"] or activity.status
    if "sort_order" in data:
        activity.sort_order = data["sort_order"]
    activity.save()
    return Response(_activity_payload(activity))


# ---------- Jurisdictions ----------
@api_view(["POST"])
@permission_classes([IsAuthenticated, HasHubPermission])
def hub_calculator_jurisdiction_list_create(request):
    hub_calculator_jurisdiction_list_create.required_permission = "config.calculator"
    data = request.data
    id_val = (data.get("id") or "").strip() or None
    label = (data.get("label") or "").strip()
    if not label:
        return Response({"label": ["This field is required."]}, status=status.HTTP_400_BAD_REQUEST)
    if not id_val:
        id_val = label.lower().replace(" ", "_")[:50]
    if Jurisdiction.objects.filter(id=id_val).exists():
        return Response({"id": ["Jurisdiction with this id already exists."]}, status=status.HTTP_400_BAD_REQUEST)
    base_price = data.get("base_price") is not None and int(data["base_price"]) or data.get("basePrice")
    if base_price is None:
        return Response({"base_price": ["This field is required."]}, status=status.HTTP_400_BAD_REQUEST)
    jurisdiction = Jurisdiction.objects.create(
        id=id_val,
        label=label,
        description=(data.get("description") or "").strip() or None,
        base_price=int(base_price),
        status=data.get("status") or "published",
    )
    return Response(_jurisdiction_payload(jurisdiction), status=status.HTTP_201_CREATED)


@api_view(["PATCH", "DELETE"])
@permission_classes([IsAuthenticated, HasHubPermission])
def hub_calculator_jurisdiction_detail(request, pk):
    hub_calculator_jurisdiction_detail.required_permission = "config.calculator"
    try:
        jurisdiction = Jurisdiction.objects.get(pk=pk)
    except Jurisdiction.DoesNotExist:
        return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
    if request.method == "DELETE":
        jurisdiction.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    data = request.data
    if "label" in data:
        jurisdiction.label = (data["label"] or "").strip() or jurisdiction.label
    if "description" in data:
        jurisdiction.description = (data["description"] or "").strip() or None
    if "base_price" in data or "basePrice" in data:
        jurisdiction.base_price = int(data.get("base_price") or data.get("basePrice") or jurisdiction.base_price)
    if "status" in data:
        jurisdiction.status = data["status"] or jurisdiction.status
    jurisdiction.save()
    return Response(_jurisdiction_payload(jurisdiction))


# ---------- Calculator services (additional services) ----------
@api_view(["POST"])
@permission_classes([IsAuthenticated, HasHubPermission])
def hub_calculator_service_list_create(request):
    hub_calculator_service_list_create.required_permission = "config.calculator"
    data = request.data
    service_id = data.get("service_id")
    if not service_id:
        return Response({"service_id": ["This field is required."]}, status=status.HTTP_400_BAD_REQUEST)
    from cms.models import Service
    try:
        service = Service.objects.get(pk=service_id)
    except Service.DoesNotExist:
        return Response({"service_id": ["Service not found."]}, status=status.HTTP_400_BAD_REQUEST)
    label = (data.get("label") or "").strip()
    if not label:
        return Response({"label": ["This field is required."]}, status=status.HTTP_400_BAD_REQUEST)
    price = data.get("price")
    if price is None:
        return Response({"price": ["This field is required."]}, status=status.HTTP_400_BAD_REQUEST)
    calc_svc = CalculatorService.objects.create(
        service=service,
        label=label,
        price=int(price),
        per=(data.get("per") or "").strip() or "one-time",
        status=data.get("status") or "published",
        sort_order=data.get("sort_order") or 0,
    )
    return Response(_calc_service_payload(calc_svc), status=status.HTTP_201_CREATED)


@api_view(["PATCH", "DELETE"])
@permission_classes([IsAuthenticated, HasHubPermission])
def hub_calculator_service_detail(request, pk):
    hub_calculator_service_detail.required_permission = "config.calculator"
    try:
        calc_svc = CalculatorService.objects.select_related("service").get(pk=pk)
    except CalculatorService.DoesNotExist:
        return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
    if request.method == "DELETE":
        calc_svc.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    data = request.data
    if "service_id" in data and data["service_id"]:
        from cms.models import Service
        try:
            calc_svc.service = Service.objects.get(pk=data["service_id"])
        except Service.DoesNotExist:
            pass
    if "label" in data:
        calc_svc.label = (data["label"] or "").strip() or calc_svc.label
    if "price" in data:
        calc_svc.price = int(data["price"])
    if "per" in data:
        calc_svc.per = (data["per"] or "").strip() or "one-time"
    if "status" in data:
        calc_svc.status = data["status"] or calc_svc.status
    if "sort_order" in data:
        calc_svc.sort_order = data["sort_order"]
    calc_svc.save()
    return Response(_calc_service_payload(CalculatorService.objects.select_related("service").get(pk=pk)))


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def hub_search_suggestions(request):
    qs = SearchSuggestion.objects.filter(status="published").order_by("sort_order")
    return Response([{"id": str(s.id), "title": s.title, "description": s.description, "type": s.type, "href": s.href, "status": s.status} for s in qs])
