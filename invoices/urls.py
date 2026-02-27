from django.urls import path
from . import views

urlpatterns = [
    path("", views.invoice_list_create),
    path("<uuid:pk>/", views.invoice_detail),
    path("<uuid:pk>/status/", views.invoice_status),
    path("<uuid:pk>/download/", views.invoice_download),
    path("<uuid:pk>/send_email/", views.invoice_send_email),
]
