from django.urls import path
from . import views

urlpatterns = [
    path("chat/stream/", views.chat_stream),
]
