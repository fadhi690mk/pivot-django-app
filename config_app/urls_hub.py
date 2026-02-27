from django.urls import path
from . import views_hub

urlpatterns = [
    path("calculator/", views_hub.hub_calculator_config),
    path("calculator/activities/", views_hub.hub_calculator_activity_list_create),
    path("calculator/activities/<str:pk>/", views_hub.hub_calculator_activity_detail),
    path("calculator/jurisdictions/", views_hub.hub_calculator_jurisdiction_list_create),
    path("calculator/jurisdictions/<str:pk>/", views_hub.hub_calculator_jurisdiction_detail),
    path("calculator/services/", views_hub.hub_calculator_service_list_create),
    path("calculator/services/<uuid:pk>/", views_hub.hub_calculator_service_detail),
    path("search-suggestions/", views_hub.hub_search_suggestions),
]
