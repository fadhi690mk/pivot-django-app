from django.urls import path
from .views import ProfileDetail, ProfileList

urlpatterns = [
    path('profiles/', ProfileList.as_view(), name='profile-list'),
    path('profiles/<int:pk>/', ProfileDetail.as_view()),
]