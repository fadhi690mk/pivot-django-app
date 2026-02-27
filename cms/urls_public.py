from django.urls import path
from . import views_public

urlpatterns = [
    path("search/", views_public.global_search),
    path("hero/", views_public.hero_list),
    path("clients/", views_public.client_list),
    path("agencies/", views_public.agency_list),
    path("testimonials/", views_public.testimonial_list),
    path("faqs/", views_public.faq_list),
    path("services/", views_public.service_list),
    path("services/<slug:slug>/", views_public.service_detail),
    path("services/<slug:service_slug>/sub-services/", views_public.subservice_list),
    path("services/<slug:service_slug>/<slug:sub_slug>/", views_public.subservice_detail),
    path("team/", views_public.team_list),
    path("blog/", views_public.blog_list),
    path("blog/<slug:slug>/", views_public.blog_detail),
    path("news/", views_public.news_list),
    path("news/<slug:slug>/", views_public.news_detail),
]
