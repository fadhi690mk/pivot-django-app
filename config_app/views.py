from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from .models import BusinessActivity, Jurisdiction, CalculatorService, SearchSuggestion


@api_view(["GET"])
@permission_classes([AllowAny])
def calculator_config(request):
    activities = BusinessActivity.objects.filter(status="published").order_by("sort_order")
    jurisdictions = Jurisdiction.objects.filter(status="published")
    services = CalculatorService.objects.filter(status="published").select_related("service").order_by("sort_order")
    return Response({
        "activities": [{"id": a.id, "label": a.label, "icon": a.icon} for a in activities],
        "jurisdictions": [
            {"id": j.id, "label": j.label, "description": j.description, "base_price": j.base_price}
            for j in jurisdictions
        ],
        "additional_services": [
            {"id": str(s.id), "label": s.label, "price": s.price, "per": s.per}
            for s in services
        ],
    })


@api_view(["GET"])
@permission_classes([AllowAny])
def search_suggestions(request):
    qs = SearchSuggestion.objects.filter(status="published").order_by("sort_order")
    return Response([{"id": str(s.id), "title": s.title, "description": s.description, "type": s.type, "href": s.href} for s in qs])
