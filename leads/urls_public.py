from django.urls import path
from . import views

urlpatterns = [
    path("", views.public_lead_create),
    path("<str:pk>/", views.public_lead_update),
]
