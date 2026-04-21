from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.db.models import F, Prefetch, Q

from .models import HeroSlide, Client, GovernmentAgency, Testimonial, FAQ, Service, SubService, BlogPost, NewsItem
from accounts.models import HubUser
from .serializers import (
    HeroSlideSerializer, ClientSerializer, GovernmentAgencySerializer, TestimonialSerializer, FAQSerializer,
    ServiceListSerializer, ServiceDetailSerializer, SubServiceListSerializer, SubServiceDetailSerializer,
    BlogPostListSerializer, BlogPostDetailSerializer, NewsItemListSerializer, NewsItemDetailSerializer,
    TeamLeadSerializer,
)


@api_view(["GET"])
@permission_classes([AllowAny])
def hero_list(request):
    qs = HeroSlide.objects.filter(status="published").order_by("sort_order")
    return Response(HeroSlideSerializer(qs, many=True).data)


@api_view(["GET"])
@permission_classes([AllowAny])
def client_list(request):
    qs = Client.objects.filter(status="published", is_deleted=False).order_by("sort_order")
    return Response(ClientSerializer(qs, many=True).data)


@api_view(["GET"])
@permission_classes([AllowAny])
def agency_list(request):
    qs = GovernmentAgency.objects.filter(status="published", is_deleted=False).order_by("sort_order")
    return Response(GovernmentAgencySerializer(qs, many=True).data)


@api_view(["GET"])
@permission_classes([AllowAny])
def testimonial_list(request):
    qs = Testimonial.objects.filter(status="published", is_deleted=False).order_by("sort_order")
    return Response(TestimonialSerializer(qs, many=True).data)


@api_view(["GET"])
@permission_classes([AllowAny])
def faq_list(request):
    category = request.query_params.get("category", "global")
    qs = FAQ.objects.filter(category=category, status="published", is_deleted=False).order_by("sort_order")
    return Response(FAQSerializer(qs, many=True).data)


@api_view(["GET"])
@permission_classes([AllowAny])
def service_list(request):
    qs = (
        Service.objects.filter(status="published", is_deleted=False)
        .prefetch_related(
            Prefetch(
                "sub_services",
                queryset=SubService.objects.filter(is_deleted=False).order_by("sort_order"),
            )
        )
        .order_by("sort_order")
    )
    service_type = request.query_params.get("service_type")
    if service_type:
        qs = qs.filter(service_type=service_type)
    return Response({"results": ServiceListSerializer(qs, many=True).data})


@api_view(["GET"])
@permission_classes([AllowAny])
def service_detail(request, slug):
    try:
        s = Service.objects.prefetch_related(
            "benefits", "required_documents", "process_steps", "price_tiers__features",
            "faqs", "target_users", "deliverables", "sub_services", "related_services"
        ).select_related("team_lead").get(slug=slug, status="published", is_deleted=False)
    except Service.DoesNotExist:
        return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
    return Response(ServiceDetailSerializer(s).data)


@api_view(["GET"])
@permission_classes([AllowAny])
def subservice_list(request, service_slug):
    try:
        service = Service.objects.get(slug=service_slug, status="published", is_deleted=False)
    except Service.DoesNotExist:
        return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
    qs = SubService.objects.filter(parent_service=service, status="published", is_deleted=False).order_by("sort_order")
    return Response(SubServiceListSerializer(qs, many=True).data)


@api_view(["GET"])
@permission_classes([AllowAny])
def subservice_detail(request, service_slug, sub_slug):
    try:
        sub = SubService.objects.prefetch_related(
            "eligibility", "benefits", "required_documents",
            "process_steps__documents", "deliverables",
            "price_tiers__features", "faqs",
        ).select_related("parent_service", "team_lead").get(
            parent_service__slug=service_slug, slug=sub_slug, status="published", is_deleted=False
        )
    except SubService.DoesNotExist:
        return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
    return Response(SubServiceDetailSerializer(sub).data)


@api_view(["GET"])
@permission_classes([AllowAny])
def team_list(request):
    qs = (
        HubUser.objects.filter(show_on_website=True, is_deleted=False)
        .prefetch_related("specializations", "led_services")
        .order_by("department", "sort_order")
    )
    out = []
    for u in qs:
        out.append({
            "id": str(u.id),
            "name": u.name,
            "role": u.job_title,
            "job_title": u.job_title,
            "department": u.department or "team",
            "bio": u.bio or "",
            "image": u.image.url if u.image else None,
            "email": getattr(u, "email", None),
            "phone": u.phone or "",
            "specializations": list(u.specializations.order_by("sort_order").values_list("text", flat=True)),
            "linkedServices": [s.slug for s in u.led_services.all()],
        })
    return Response(out)


@api_view(["GET"])
@permission_classes([AllowAny])
def blog_list(request):
    qs = BlogPost.objects.filter(status="published", is_deleted=False).select_related("category").prefetch_related("tags").order_by("-published_at")
    category = request.query_params.get("category")  # slug or uuid of Service
    if category:
        if len(category) == 36 and "-" in category:
            qs = qs.filter(category_id=category)
        else:
            qs = qs.filter(category__slug=category)
    from rest_framework.pagination import PageNumberPagination
    paginator = PageNumberPagination()
    paginator.page_size = 20
    page = paginator.paginate_queryset(qs, request)
    return paginator.get_paginated_response(BlogPostListSerializer(page, many=True).data)


@api_view(["GET"])
@permission_classes([AllowAny])
def blog_detail(request, slug):
    try:
        post = BlogPost.objects.select_related("category", "author").prefetch_related("tags").get(
            slug=slug, status="published", is_deleted=False
        )
    except BlogPost.DoesNotExist:
        return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
    BlogPost.objects.filter(pk=post.pk).update(views=F("views") + 1)
    post.refresh_from_db()
    return Response(BlogPostDetailSerializer(post).data)


@api_view(["GET"])
@permission_classes([AllowAny])
def news_list(request):
    qs = NewsItem.objects.filter(status="published", is_deleted=False).order_by("-published_at")
    from rest_framework.pagination import PageNumberPagination
    paginator = PageNumberPagination()
    paginator.page_size = 20
    page = paginator.paginate_queryset(qs, request)
    return paginator.get_paginated_response(NewsItemListSerializer(page, many=True).data)


@api_view(["GET"])
@permission_classes([AllowAny])
def news_detail(request, slug):
    try:
        item = NewsItem.objects.get(slug=slug, status="published", is_deleted=False)
    except NewsItem.DoesNotExist:
        return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
    return Response(NewsItemDetailSerializer(item).data)


def _relevance(item, term):
    """Simple relevance: title start (3), title contains (2), slug contains (2), else 1."""
    t = (item.get("title") or "").lower()
    s = (item.get("slug") or "").lower()
    term = term.lower()
    if t.startswith(term) or term in t.split()[0:1]:
        return 3
    if term in t:
        return 2
    if term in s:
        return 2
    return 1


@api_view(["GET"])
@permission_classes([AllowAny])
def global_search(request):
    """
    Global search across public marketing models. Returns only title, slug, type, root_path.
    Frontend must build URL as root_path + slug (always root-based, e.g. /services/visa-setup).
    """
    q = (request.query_params.get("q") or "").strip()[:200]
    if not q:
        return Response({"results": []})

    results = []
    limit_per_type = 6
    term = q

    # Services: root_path = /services/
    service_q = Q(title__icontains=term) | Q(slug__icontains=term) | Q(short_title__icontains=term) | Q(tagline__icontains=term) | Q(description__icontains=term) | Q(long_description__icontains=term)
    for s in Service.objects.filter(service_q, status="published", is_deleted=False).only("title", "slug")[:limit_per_type]:
        results.append({
            "title": s.title,
            "slug": s.slug or "",
            "type": "service",
            "root_path": "/services/",
        })

    # SubServices: root_path = /services/<parent_slug>/ (URL: /services/visa/employment-visa)
    sub_q = Q(title__icontains=term) | Q(slug__icontains=term) | Q(tagline__icontains=term) | Q(description__icontains=term) | Q(long_description__icontains=term)
    for sub in SubService.objects.filter(sub_q, status="published", is_deleted=False).select_related("parent_service").only("title", "slug", "parent_service__slug")[:limit_per_type]:
        parent_slug = (sub.parent_service.slug or "").strip()
        root_path = f"/services/{parent_slug}/" if parent_slug else "/services/"
        results.append({
            "title": sub.title,
            "slug": sub.slug or "",
            "type": "subservice",
            "root_path": root_path,
        })

    # Blog: root_path = /blog/
    blog_q = Q(title__icontains=term) | Q(slug__icontains=term) | Q(excerpt__icontains=term) | Q(content__icontains=term)
    for b in BlogPost.objects.filter(blog_q, status="published", is_deleted=False).only("title", "slug")[:limit_per_type]:
        results.append({
            "title": b.title,
            "slug": b.slug or "",
            "type": "blog",
            "root_path": "/blog/",
        })

    # News: root_path = /news/
    news_q = Q(title__icontains=term) | Q(slug__icontains=term) | Q(excerpt__icontains=term) | Q(content__icontains=term)
    for n in NewsItem.objects.filter(news_q, status="published", is_deleted=False).only("title", "slug")[:limit_per_type]:
        results.append({
            "title": n.title,
            "slug": n.slug or "",
            "type": "news",
            "root_path": "/news/",
        })

    # Sort by relevance and take top 15
    results.sort(key=lambda r: (-_relevance(r, term), (r["title"] or "").lower()))
    return Response({"results": results[:15]})
