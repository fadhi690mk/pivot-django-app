from django.urls import path
from . import views

urlpatterns = [
    path("", views.audit_list),
    path("users/", views.audit_users),
]
