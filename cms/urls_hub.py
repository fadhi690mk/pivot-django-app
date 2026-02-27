from django.urls import path
from . import views_hub

urlpatterns = [
    path("upload-image/", views_hub.hub_upload_image),
    path("hero/", views_hub.hub_hero_list),
    path("hero/<uuid:pk>/", views_hub.hub_hero_detail),
    path("clients/", views_hub.hub_client_list),
    path("clients/<uuid:pk>/", views_hub.hub_client_detail),
    path("agencies/", views_hub.hub_agency_list),
    path("agencies/<uuid:pk>/", views_hub.hub_agency_detail),
    path("testimonials/", views_hub.hub_testimonial_list),
    path("testimonials/<uuid:pk>/", views_hub.hub_testimonial_detail),
    path("faqs/", views_hub.hub_faq_list),
    path("faqs/<uuid:pk>/", views_hub.hub_faq_detail),
    path("services/", views_hub.hub_service_list),
    path("services/<slug:slug>/", views_hub.hub_service_detail),
    path("services/<slug:service_slug>/sub-services/", views_hub.hub_subservice_list),
    path("services/<slug:service_slug>/sub-services/<slug:sub_slug>/", views_hub.hub_subservice_detail),
    path("team/", views_hub.hub_team_list),
    path("team/<uuid:pk>/", views_hub.hub_team_detail),
    path("blog/", views_hub.hub_blog_list),
    path("blog/<slug:slug>/", views_hub.hub_blog_detail),
    path("news/", views_hub.hub_news_list),
    path("news/<slug:slug>/", views_hub.hub_news_detail),
]
