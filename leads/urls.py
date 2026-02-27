from django.urls import path
from . import views

urlpatterns = [
    path("", views.lead_list),
    path("bulk/", views.lead_bulk_create),
    path("<str:pk>/", views.lead_detail),
    path("<str:pk>/notes/", views.lead_add_note),
    path("<str:pk>/assign/", views.lead_assign),
]
