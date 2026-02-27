from django.urls import path
from . import views

urlpatterns = [
    path("calculator/", views.calculator_config),
    path("search-suggestions/", views.search_suggestions),
]
