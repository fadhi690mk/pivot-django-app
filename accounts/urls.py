from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from . import views

urlpatterns = [
    path("auth/login/", views.login),
    path("auth/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("auth/logout/", views.logout),
    path("auth/register-fcm/", views.register_fcm),
    path("auth/me/", views.me),
    path("auth/menu/", views.menu),
    path("users/", views.user_list),
    path("roles/", views.role_list),
    path("roles/<uuid:pk>/", views.role_detail),
]
