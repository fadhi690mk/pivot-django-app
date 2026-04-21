"""
Hub-authenticated CMS endpoints. Same data shape as public but require JWT.
Hub can see draft/archived content; public endpoints filter by status.
"""
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from accounts.permissions import HasHubPermission
from django.db.models import Prefetch
from audit.utils import log_audit

from django.db import transaction
from core.image_utils import save_uploaded_image_as_webp
from .models import (
    HeroSlide, Client, GovernmentAgency, Testimonial, FAQ, Service, SubService, BlogPost, NewsItem,
    ServiceBenefit, ServiceDocument, ServiceProcessStep, ServiceDeliverable,
    ServicePriceTier, PriceTierFeature, ServiceFAQ, ServiceTargetUser,
    SubServiceEligibility, SubServiceBenefit, SubServiceDocument,
    SubServiceProcessStep, SubServiceProcessStepDocument, SubServiceDeliverable,
    SubServicePriceTier, SubServicePriceTierFeature, SubServiceFAQ,
)
from accounts.models import HubUser, UserRole
from .serializers import (
    HeroSlideSerializer, HeroSlideWriteSerializer,
    ClientSerializer, ClientWriteSerializer,
    GovernmentAgencySerializer, GovernmentAgencyWriteSerializer,
    TestimonialSerializer, TestimonialWriteSerializer,
    FAQSerializer, FAQWriteSerializer,
    ServiceListSerializer, ServiceDetailSerializer, SubServiceListSerializer, SubServiceDetailSerializer,
    BlogPostListSerializer, BlogPostDetailSerializer, BlogPostWriteSerializer,
    NewsItemListSerializer, NewsItemDetailSerializer, NewsItemWriteSerializer,
    TeamLeadSerializer,
    HubStaffListSerializer,
    HubStaffWriteSerializer,
)


def _hero_qs():
    return HeroSlide.objects.filter(is_deleted=False).prefetch_related("key_services", "stats").order_by("sort_order")


def _client_qs():
    return Client.objects.filter(is_deleted=False).order_by("sort_order")


def _agency_qs():
    return GovernmentAgency.objects.filter(is_deleted=False).order_by("sort_order")


def _testimonial_qs():
    return Testimonial.objects.filter(is_deleted=False).order_by("sort_order")


def _faq_qs(category="global"):
    return FAQ.objects.filter(category=category, is_deleted=False).order_by("sort_order")


def _service_qs():
    return Service.objects.filter(is_deleted=False).order_by("sort_order")


@api_view(["POST"])
@permission_classes([IsAuthenticated, HasHubPermission])
def hub_upload_image(request):
    hub_upload_image.required_permission = "cms.hero.edit"
    """Accept an image file; save as WebP and return the path for use in hero/CMS."""
    file = request.FILES.get("file") or request.FILES.get("image")
    if not file:
        return Response({"detail": "No file provided. Use 'file' or 'image'."}, status=status.HTTP_400_BAD_REQUEST)
    upload_to = request.data.get("upload_to", "hero/")
    if not isinstance(upload_to, str):
        upload_to = "hero/"
    try:
        path = save_uploaded_image_as_webp(file, upload_to=upload_to)
        return Response({"path": path})
    except Exception as e:
        return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated, HasHubPermission])
def hub_hero_list(request):
    hub_hero_list.required_permissions = {"GET": "cms.hero.edit", "POST": "cms.hero.edit"}
    if request.method == "POST":
        serializer = HeroSlideWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        slide = serializer.save()
        log_audit(request, "create", "cms", f"Hero slide {slide.id}", str(slide.id), "Hero slide created")
        qs = HeroSlide.objects.filter(pk=slide.pk).prefetch_related("key_services", "stats")
        return Response(HeroSlideSerializer(qs.first(), many=False).data, status=status.HTTP_201_CREATED)
    return Response(HeroSlideSerializer(_hero_qs(), many=True).data)


@api_view(["GET", "PATCH", "DELETE"])
@permission_classes([IsAuthenticated, HasHubPermission])
def hub_hero_detail(request, pk):
    hub_hero_detail.required_permissions = {"GET": "cms.hero.edit", "PATCH": "cms.hero.edit", "DELETE": "cms.hero.edit"}
    try:
        slide = HeroSlide.objects.prefetch_related("key_services", "stats").get(pk=pk, is_deleted=False)
    except HeroSlide.DoesNotExist:
        return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
    if request.method == "DELETE":
        slide.is_deleted = True
        slide.save()
        log_audit(request, "delete", "cms", f"Hero slide {slide.id}", str(slide.id), "Hero slide deleted")
        return Response(status=status.HTTP_204_NO_CONTENT)
    if request.method == "PATCH":
        serializer = HeroSlideWriteSerializer(slide, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        slide = serializer.save()
        log_audit(request, "update", "cms", f"Hero slide {slide.id}", str(slide.id), "Hero slide updated")
        slide.refresh_from_db()
        slide = HeroSlide.objects.prefetch_related("key_services", "stats").get(pk=slide.pk)
        return Response(HeroSlideSerializer(slide).data)
    return Response(HeroSlideSerializer(slide).data)


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated, HasHubPermission])
def hub_client_list(request):
    hub_client_list.required_permissions = {"GET": "cms.clients.edit", "POST": "cms.clients.edit"}
    if request.method == "POST":
        serializer = ClientWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        client = serializer.save()
        log_audit(request, "create", "cms", f"Client {getattr(client, 'title', client.id)}", str(client.id), "Client created")
        return Response(ClientSerializer(client).data, status=status.HTTP_201_CREATED)
    return Response(ClientSerializer(_client_qs(), many=True).data)


@api_view(["GET", "PATCH", "DELETE"])
@permission_classes([IsAuthenticated, HasHubPermission])
def hub_client_detail(request, pk):
    hub_client_detail.required_permissions = {"GET": "cms.clients.edit", "PATCH": "cms.clients.edit", "DELETE": "cms.clients.edit"}
    try:
        client = Client.objects.get(pk=pk, is_deleted=False)
    except Client.DoesNotExist:
        return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
    if request.method == "DELETE":
        client.is_deleted = True
        client.save()
        log_audit(request, "delete", "cms", f"Client {getattr(client, 'title', client.id)}", str(client.id), "Client deleted")
        return Response(status=status.HTTP_204_NO_CONTENT)
    if request.method == "PATCH":
        serializer = ClientWriteSerializer(client, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        client = serializer.save()
        log_audit(request, "update", "cms", f"Client {getattr(client, 'title', client.id)}", str(client.id), "Client updated")
        return Response(ClientSerializer(client).data)
    return Response(ClientSerializer(client).data)


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated, HasHubPermission])
def hub_agency_list(request):
    hub_agency_list.required_permissions = {"GET": "cms.pages.edit", "POST": "cms.pages.edit"}
    if request.method == "POST":
        serializer = GovernmentAgencyWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        agency = serializer.save()
        log_audit(request, "create", "cms", f"Government agency {getattr(agency, 'title', agency.id)}", str(agency.id), "Government agency created")
        return Response(GovernmentAgencySerializer(agency).data, status=status.HTTP_201_CREATED)
    return Response(GovernmentAgencySerializer(_agency_qs(), many=True).data)


@api_view(["GET", "PATCH", "DELETE"])
@permission_classes([IsAuthenticated, HasHubPermission])
def hub_agency_detail(request, pk):
    hub_agency_detail.required_permissions = {"GET": "cms.pages.edit", "PATCH": "cms.pages.edit", "DELETE": "cms.pages.edit"}
    try:
        agency = GovernmentAgency.objects.get(pk=pk, is_deleted=False)
    except GovernmentAgency.DoesNotExist:
        return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
    if request.method == "DELETE":
        agency.is_deleted = True
        agency.save()
        log_audit(request, "delete", "cms", f"Government agency {getattr(agency, 'title', agency.id)}", str(agency.id), "Government agency deleted")
        return Response(status=status.HTTP_204_NO_CONTENT)
    if request.method == "PATCH":
        serializer = GovernmentAgencyWriteSerializer(agency, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        agency = serializer.save()
        log_audit(request, "update", "cms", f"Government agency {getattr(agency, 'title', agency.id)}", str(agency.id), "Government agency updated")
        return Response(GovernmentAgencySerializer(agency).data)
    return Response(GovernmentAgencySerializer(agency).data)


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated, HasHubPermission])
def hub_testimonial_list(request):
    hub_testimonial_list.required_permissions = {"GET": "cms.testimonials.edit", "POST": "cms.testimonials.edit"}
    if request.method == "POST":
        serializer = TestimonialWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        testimonial = serializer.save()
        log_audit(request, "create", "cms", f"Testimonial {getattr(testimonial, 'name', testimonial.id)}", str(testimonial.id), "Testimonial created")
        return Response(TestimonialSerializer(testimonial).data, status=status.HTTP_201_CREATED)
    return Response(TestimonialSerializer(_testimonial_qs(), many=True).data)


@api_view(["GET", "PATCH", "DELETE"])
@permission_classes([IsAuthenticated, HasHubPermission])
def hub_testimonial_detail(request, pk):
    hub_testimonial_detail.required_permissions = {"GET": "cms.testimonials.edit", "PATCH": "cms.testimonials.edit", "DELETE": "cms.testimonials.edit"}
    try:
        testimonial = Testimonial.objects.get(pk=pk, is_deleted=False)
    except Testimonial.DoesNotExist:
        return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
    if request.method == "DELETE":
        testimonial.is_deleted = True
        testimonial.save()
        log_audit(request, "delete", "cms", f"Testimonial {getattr(testimonial, 'name', testimonial.id)}", str(testimonial.id), "Testimonial deleted")
        return Response(status=status.HTTP_204_NO_CONTENT)
    if request.method == "PATCH":
        serializer = TestimonialWriteSerializer(testimonial, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        testimonial = serializer.save()
        log_audit(request, "update", "cms", f"Testimonial {getattr(testimonial, 'name', testimonial.id)}", str(testimonial.id), "Testimonial updated")
        return Response(TestimonialSerializer(testimonial).data)
    return Response(TestimonialSerializer(testimonial).data)


def _faq_qs_all():
    return FAQ.objects.filter(is_deleted=False).order_by("category", "sort_order")


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated, HasHubPermission])
def hub_faq_list(request):
    hub_faq_list.required_permissions = {"GET": "cms.faq.edit", "POST": "cms.faq.edit"}
    if request.method == "POST":
        serializer = FAQWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        faq = serializer.save()
        log_audit(request, "create", "cms", f"FAQ {getattr(faq, 'question', faq.id)[:50]}", str(faq.id), "FAQ created")
        return Response(FAQSerializer(faq).data, status=status.HTTP_201_CREATED)
    category = request.query_params.get("category", "global")
    if category == "all":
        return Response(FAQSerializer(_faq_qs_all(), many=True).data)
    return Response(FAQSerializer(_faq_qs(category), many=True).data)


@api_view(["GET", "PATCH", "DELETE"])
@permission_classes([IsAuthenticated, HasHubPermission])
def hub_faq_detail(request, pk):
    hub_faq_detail.required_permissions = {"GET": "cms.faq.edit", "PATCH": "cms.faq.edit", "DELETE": "cms.faq.edit"}
    try:
        faq = FAQ.objects.get(pk=pk, is_deleted=False)
    except FAQ.DoesNotExist:
        return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
    if request.method == "DELETE":
        faq.is_deleted = True
        faq.save()
        log_audit(request, "delete", "cms", f"FAQ {getattr(faq, 'question', faq.id)[:50]}", str(faq.id), "FAQ deleted")
        return Response(status=status.HTTP_204_NO_CONTENT)
    if request.method == "PATCH":
        serializer = FAQWriteSerializer(faq, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        faq = serializer.save()
        log_audit(request, "update", "cms", f"FAQ {getattr(faq, 'question', faq.id)[:50]}", str(faq.id), "FAQ updated")
        return Response(FAQSerializer(faq).data)
    return Response(FAQSerializer(faq).data)


def _apply_service_sections(service, data):
    """Replace all section data for a service from payload (lists/dicts)."""
    if "benefits" in data and data["benefits"] is not None:
        service.benefits.all().delete()
        for i, text in enumerate(data["benefits"]):
            if text:
                ServiceBenefit.objects.create(service=service, text=str(text)[:500], sort_order=i)
    if "required_documents" in data and data["required_documents"] is not None:
        service.required_documents.all().delete()
        for i, text in enumerate(data["required_documents"]):
            if text:
                ServiceDocument.objects.create(service=service, text=str(text)[:500], sort_order=i)
    if "process_steps" in data and data["process_steps"] is not None:
        service.process_steps.all().delete()
        for i, step in enumerate(data["process_steps"]):
            if isinstance(step, dict):
                ServiceProcessStep.objects.create(
                    service=service,
                    step_number=step.get("step_number") or step.get("step") or i + 1,
                    title=(step.get("title") or "")[:255],
                    description=step.get("description") or "",
                    timeline=(step.get("timeline") or "")[:100] or None,
                    sort_order=i,
                )
    if "deliverables" in data and data["deliverables"] is not None:
        service.deliverables.all().delete()
        for i, text in enumerate(data["deliverables"]):
            if text:
                ServiceDeliverable.objects.create(service=service, text=str(text)[:500], sort_order=i)
    if "price_tiers" in data and data["price_tiers"] is not None:
        service.price_tiers.all().delete()
        for i, pt in enumerate(data["price_tiers"]):
            if isinstance(pt, dict):
                tier = ServicePriceTier.objects.create(
                    service=service,
                    name=(pt.get("name") or "")[:100],
                    price=(pt.get("price") or "")[:50],
                    description=(pt.get("description") or "")[:255] or None,
                    is_popular=bool(pt.get("is_popular") or pt.get("popular")),
                    sort_order=i,
                )
                for j, feat in enumerate(pt.get("features") or []):
                    text = feat if isinstance(feat, str) else (feat.get("text") or "")
                    if text:
                        PriceTierFeature.objects.create(price_tier=tier, text=str(text)[:500], sort_order=j)
    if "faqs" in data and data["faqs"] is not None:
        service.faqs.all().delete()
        for i, faq in enumerate(data["faqs"]):
            if isinstance(faq, dict) and faq.get("question"):
                ServiceFAQ.objects.create(
                    service=service,
                    question=faq.get("question", ""),
                    answer=faq.get("answer", ""),
                    sort_order=i,
                )
    if "target_users" in data and data["target_users"] is not None:
        service.target_users.all().delete()
        for i, text in enumerate(data["target_users"]):
            if text:
                ServiceTargetUser.objects.create(service=service, text=str(text)[:255], sort_order=i)
    if "related_services" in data and data["related_services"] is not None:
        ids = [x for x in data["related_services"] if x]
        try:
            related = list(Service.objects.filter(id__in=ids, is_deleted=False).values_list("id", flat=True))
            service.related_services.set(related)
        except Exception:
            pass


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated, HasHubPermission])
def hub_service_list(request):
    hub_service_list.required_permissions = {"GET": "cms.services.view", "POST": "cms.services.edit"}
    if request.method == "POST":
        data = request.data
        slug = (data.get("slug") or "").strip()
        # Slug is optional; model save() auto-generates from title if blank and ensures uniqueness
        with transaction.atomic():
            service = Service.objects.create(
                title=(data.get("title") or "")[:255],
                service_type=(data.get("service_type") or "service")[:20],
                slug=slug or "",
                short_title=(data.get("short_title") or data.get("title") or "")[:100],
                tagline=(data.get("tagline") or "")[:255],
                description=data.get("description") or "",
                long_description=data.get("long_description") or data.get("description") or "",
                category=(data.get("category") or "general")[:20],
                starting_price=(data.get("starting_price") or "")[:50],
                timeline=(data.get("timeline") or "")[:100],
                status=(data.get("status") or "published")[:15],
                offer_badge=(data.get("offer_badge") or "")[:100],
                sort_order=int(data.get("sort_order", 0)),
                icon=(data.get("icon") or "")[:64],
            )
            team_lead_id = data.get("team_lead_id") or data.get("team_lead")
            if team_lead_id:
                try:
                    service.team_lead_id = team_lead_id
                    service.save(update_fields=["team_lead_id"])
                except Exception:
                    pass
            for k in ("meta_title", "meta_description", "meta_keywords"):
                if data.get(k) is not None:
                    setattr(service, k, (data.get(k) or "")[:255] if k != "meta_description" else (data.get(k) or "")[:500])
            service.save()
            _apply_service_sections(service, data)
        service.refresh_from_db()
        service = Service.objects.prefetch_related(
            "benefits", "required_documents", "process_steps", "price_tiers__features",
            "faqs", "target_users", "deliverables", "sub_services", "related_services"
        ).select_related("team_lead").get(pk=service.pk)
        log_audit(request, "create", "cms", f"Service {service.title}", str(service.id), "Service created")
        return Response(ServiceDetailSerializer(service).data, status=status.HTTP_201_CREATED)
    qs = _service_qs().prefetch_related(
        Prefetch(
            "sub_services",
            queryset=SubService.objects.filter(is_deleted=False).order_by("sort_order"),
        )
    )
    # get service_type from query params
    service_type = request.query_params.get("service_type")

    if service_type:
        qs = qs.filter(service_type=service_type)

    return Response({"results": ServiceListSerializer(qs, many=True).data})


@api_view(["GET", "PATCH", "DELETE"])
@permission_classes([IsAuthenticated, HasHubPermission])
def hub_service_detail(request, slug):
    hub_service_detail.required_permissions = {"GET": "cms.services.view", "PATCH": "cms.services.edit", "DELETE": "cms.services.edit"}
    try:
        s = Service.objects.prefetch_related(
            "benefits", "required_documents", "process_steps", "price_tiers__features",
            "faqs", "target_users", "deliverables", "sub_services", "related_services"
        ).select_related("team_lead").get(slug=slug, is_deleted=False)
    except Service.DoesNotExist:
        return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
    if request.method == "DELETE":
        s.is_deleted = True
        s.save(update_fields=["is_deleted"])
        log_audit(request, "delete", "cms", f"Service {s.title}", str(s.id), "Service deleted")
        return Response(status=status.HTTP_204_NO_CONTENT)
    if request.method == "PATCH":
        data = request.data
        with transaction.atomic():
            for attr in ("title", "slug", "short_title", "tagline", "description", "long_description",
                         "category", "starting_price", "timeline", "status", "offer_badge", "sort_order", "icon", "service_type"):
                if data.get(attr) is not None:
                    val = data[attr]
                    if attr == "sort_order":
                        try:
                            s.sort_order = int(val)
                        except (TypeError, ValueError):
                            pass
                        continue
                    if attr in ("title", "short_title", "tagline"):
                        val = (val or "")[:255] if attr != "short_title" else (val or "")[:100]
                    elif attr == "slug":
                        val = (val or "")[:100]
                    elif attr == "service_type":
                        val = (val or "service")[:20]
                    elif attr in ("category", "status"):
                        val = (val or "")[:20] if attr == "category" else (val or "published")[:15]
                    elif attr in ("starting_price", "timeline", "offer_badge"):
                        val = (val or "")[:50] if attr == "starting_price" else (val or "")[:100]
                    elif attr == "icon":
                        val = (val or "")[:64]
                    setattr(s, attr, val)
            if data.get("hero_image") is not None:
                s.hero_image = (data.get("hero_image") or "").strip() or None
            team_lead_id = data.get("team_lead_id") or data.get("team_lead")
            if team_lead_id is not None:
                try:
                    s.team_lead_id = team_lead_id or None
                except Exception:
                    pass
            for k in ("meta_title", "meta_description", "meta_keywords"):
                if data.get(k) is not None:
                    setattr(s, k, (data.get(k) or "")[:255] if k != "meta_description" else (data.get(k) or "")[:500])
            s.save()
            _apply_service_sections(s, data)
        s.refresh_from_db()
        s = Service.objects.prefetch_related(
            "benefits", "required_documents", "process_steps", "price_tiers__features",
            "faqs", "target_users", "deliverables", "sub_services", "related_services"
        ).select_related("team_lead").get(pk=s.pk)
        log_audit(request, "update", "cms", f"Service {s.title}", str(s.id), "Service updated")
        return Response(ServiceDetailSerializer(s).data)
    return Response(ServiceDetailSerializer(s).data)


def _apply_subservice_sections(sub, data):
    """Replace all section data for a sub-service from payload."""
    if "eligibility" in data and data["eligibility"] is not None:
        sub.eligibility.all().delete()
        for i, text in enumerate(data["eligibility"]):
            if text:
                SubServiceEligibility.objects.create(sub_service=sub, text=str(text)[:500], sort_order=i)
    if "benefits" in data and data["benefits"] is not None:
        sub.benefits.all().delete()
        for i, text in enumerate(data["benefits"]):
            if text:
                SubServiceBenefit.objects.create(sub_service=sub, text=str(text)[:500], sort_order=i)
    if "required_documents" in data and data["required_documents"] is not None:
        sub.required_documents.all().delete()
        for i, text in enumerate(data["required_documents"]):
            if text:
                SubServiceDocument.objects.create(sub_service=sub, text=str(text)[:500], sort_order=i)
    if "process_steps" in data and data["process_steps"] is not None:
        sub.process_steps.all().delete()
        for i, step in enumerate(data["process_steps"]):
            if isinstance(step, dict):
                ss = SubServiceProcessStep.objects.create(
                    sub_service=sub,
                    step_number=step.get("step_number") or step.get("step") or i + 1,
                    title=(step.get("title") or "")[:255],
                    description=step.get("description") or "",
                    timeline=(step.get("timeline") or "")[:100] or None,
                    sort_order=i,
                )
                for doc_text in step.get("documents") or []:
                    if doc_text:
                        SubServiceProcessStepDocument.objects.create(
                            process_step=ss, text=str(doc_text)[:500], sort_order=0
                        )
    if "deliverables" in data and data["deliverables"] is not None:
        sub.deliverables.all().delete()
        for i, text in enumerate(data["deliverables"]):
            if text:
                SubServiceDeliverable.objects.create(sub_service=sub, text=str(text)[:500], sort_order=i)
    if "price_tiers" in data and data["price_tiers"] is not None:
        sub.price_tiers.all().delete()
        for i, pt in enumerate(data["price_tiers"]):
            if isinstance(pt, dict):
                stier = SubServicePriceTier.objects.create(
                    sub_service=sub,
                    name=(pt.get("name") or "")[:100],
                    price=(pt.get("price") or "")[:50],
                    description=(pt.get("description") or "")[:255] or None,
                    is_popular=bool(pt.get("is_popular") or pt.get("popular")),
                    sort_order=i,
                )
                for j, feat in enumerate(pt.get("features") or []):
                    text = feat if isinstance(feat, str) else (feat.get("text") or "")
                    if text:
                        SubServicePriceTierFeature.objects.create(
                            price_tier=stier, text=str(text)[:500], sort_order=j
                        )
    if "faqs" in data and data["faqs"] is not None:
        sub.faqs.all().delete()
        for i, faq in enumerate(data["faqs"]):
            if isinstance(faq, dict) and faq.get("question"):
                SubServiceFAQ.objects.create(
                    sub_service=sub,
                    question=faq.get("question", ""),
                    answer=faq.get("answer", ""),
                    sort_order=i,
                )


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated, HasHubPermission])
def hub_subservice_list(request, service_slug):
    hub_subservice_list.required_permissions = {"GET": "cms.services.view", "POST": "cms.services.edit"}
    try:
        service = Service.objects.get(slug=service_slug, is_deleted=False)
    except Service.DoesNotExist:
        return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
    if request.method == "POST":
        data = request.data
        sub_slug = (data.get("slug") or "").strip()
        # Slug is optional; model save() auto-generates from title if blank and ensures uniqueness per parent
        with transaction.atomic():
            sub = SubService.objects.create(
                parent_service=service,
                title=(data.get("title") or "")[:255],
                slug=sub_slug or "",
                tagline=(data.get("tagline") or "")[:255],
                description=data.get("description") or "",
                long_description=data.get("long_description") or data.get("description") or "",
                starting_price=(data.get("starting_price") or "")[:50],
                timeline=(data.get("timeline") or "")[:100],
                status=(data.get("status") or "published")[:15],
                offer_badge=(data.get("offer_badge") or "")[:100],
                sort_order=int(data.get("sort_order", service.sub_services.filter(is_deleted=False).count())),
            )
            team_lead_id = data.get("team_lead_id") or data.get("team_lead")
            if team_lead_id:
                try:
                    sub.team_lead_id = team_lead_id
                    sub.save(update_fields=["team_lead_id"])
                except Exception:
                    pass
            for k in ("meta_title", "meta_description", "meta_keywords"):
                if data.get(k) is not None:
                    setattr(sub, k, (data.get(k) or "")[:255] if k != "meta_description" else (data.get(k) or "")[:500])
            sub.save()
            _apply_subservice_sections(sub, data)
        sub.refresh_from_db()
        sub = SubService.objects.prefetch_related(
            "eligibility", "benefits", "required_documents",
            "process_steps__documents", "deliverables",
            "price_tiers__features", "faqs",
        ).select_related("parent_service", "team_lead").get(pk=sub.pk)
        log_audit(request, "create", "cms", f"SubService {sub.title}", str(sub.id), "SubService created")
        return Response(SubServiceDetailSerializer(sub).data, status=status.HTTP_201_CREATED)
    qs = SubService.objects.filter(parent_service=service, is_deleted=False).order_by("sort_order")
    return Response(SubServiceListSerializer(qs, many=True).data)


@api_view(["GET", "PATCH", "DELETE"])
@permission_classes([IsAuthenticated, HasHubPermission])
def hub_subservice_detail(request, service_slug, sub_slug):
    hub_subservice_detail.required_permissions = {"GET": "cms.services.view", "PATCH": "cms.services.edit", "DELETE": "cms.services.edit"}
    try:
        sub = SubService.objects.prefetch_related(
            "eligibility", "benefits", "required_documents",
            "process_steps__documents", "deliverables",
            "price_tiers__features", "faqs",
        ).select_related("parent_service", "team_lead").get(
            parent_service__slug=service_slug, slug=sub_slug, is_deleted=False
        )
    except SubService.DoesNotExist:
        return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
    if request.method == "DELETE":
        sub.is_deleted = True
        sub.save(update_fields=["is_deleted"])
        log_audit(request, "delete", "cms", f"SubService {sub.title}", str(sub.id), "SubService deleted")
        return Response(status=status.HTTP_204_NO_CONTENT)
    if request.method == "PATCH":
        data = request.data
        with transaction.atomic():
            for attr in ("title", "slug", "tagline", "description", "long_description",
                         "starting_price", "timeline", "status", "offer_badge", "sort_order"):
                if data.get(attr) is not None:
                    val = data[attr]
                    if attr == "sort_order":
                        try:
                            sub.sort_order = int(val)
                        except (TypeError, ValueError):
                            pass
                        continue
                    if attr in ("title", "tagline"):
                        val = (val or "")[:255]
                    elif attr == "slug":
                        val = (val or "")[:100]
                    elif attr == "status":
                        val = (val or "published")[:15]
                    elif attr in ("starting_price", "timeline", "offer_badge"):
                        val = (val or "")[:50] if attr != "timeline" else (val or "")[:100]
                    setattr(sub, attr, val)
            if data.get("hero_image") is not None:
                sub.hero_image = (data.get("hero_image") or "").strip() or None
            team_lead_id = data.get("team_lead_id") or data.get("team_lead")
            if team_lead_id is not None:
                try:
                    sub.team_lead_id = team_lead_id or None
                except Exception:
                    pass
            for k in ("meta_title", "meta_description", "meta_keywords"):
                if data.get(k) is not None:
                    setattr(sub, k, (data.get(k) or "")[:255] if k != "meta_description" else (data.get(k) or "")[:500])
            sub.save()
            _apply_subservice_sections(sub, data)
        sub.refresh_from_db()
        sub = SubService.objects.prefetch_related(
            "eligibility", "benefits", "required_documents",
            "process_steps__documents", "deliverables",
            "price_tiers__features", "faqs",
        ).select_related("parent_service", "team_lead").get(pk=sub.pk)
        log_audit(request, "update", "cms", f"SubService {sub.title}", str(sub.id), "SubService updated")
        return Response(SubServiceDetailSerializer(sub).data)
    return Response(SubServiceDetailSerializer(sub).data)


def _hub_staff_qs():
    return (
        HubUser.objects.filter(is_deleted=False)
        .prefetch_related("roles", "specializations", "led_services", "led_subservices__parent_service")
        .order_by("sort_order", "department", "name")
    )


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated, HasHubPermission])
def hub_team_list(request):
    hub_team_list.required_permissions = {"GET": "cms.team.edit", "POST": "cms.team.edit"}
    if request.method == "POST":
        serializer = HubStaffWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        email = (data.get("email") or "").strip()
        name = (data.get("name") or "").strip()
        if not email or not name:
            return Response(
                {"detail": "name and email are required"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if HubUser.objects.filter(email__iexact=email, is_deleted=False).exists():
            return Response(
                {"detail": "A staff member with this email already exists."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        from django.contrib.auth.hashers import make_password
        from django.utils.crypto import get_random_string
        raw_password = (data.get("password") or "").strip()
        with transaction.atomic():
            user = HubUser.objects.create(
                email=email,
                name=name,
                password=make_password(raw_password or get_random_string(32)),
                job_title=(data.get("job_title") or "")[:255],
                department=(data.get("department") or "team")[:20],
                bio=data.get("bio") or "",
                phone=(data.get("phone") or "")[:30],
                show_on_website=bool(data.get("show_on_website")),
                sort_order=int(data.get("sort_order", 0)),
                meta_title=(data.get("meta_title") or "")[:255],
                meta_description=(data.get("meta_description") or "")[:500],
                meta_keywords=(data.get("meta_keywords") or "")[:255],
            )
            if data.get("image"):
                user.image = (data.get("image") or "").strip()
                user.save(update_fields=["image"])
            role_ids = data.get("role_ids") or []
            if role_ids:
                user.roles.set(UserRole.objects.filter(id__in=role_ids))
            from accounts.models import UserSpecialization
            for i, text in enumerate(data.get("specializations") or []):
                if text:
                    UserSpecialization.objects.create(user=user, text=str(text)[:255], sort_order=i)
        user.refresh_from_db()
        user = _hub_staff_qs().get(pk=user.pk)
        log_audit(request, "create", "cms", f"Team member {user.name}", str(user.id), "Team member created")
        return Response(HubStaffListSerializer(user).data, status=status.HTTP_201_CREATED)
    qs = _hub_staff_qs()
    return Response(HubStaffListSerializer(qs, many=True).data)


@api_view(["GET", "PATCH", "DELETE"])
@permission_classes([IsAuthenticated, HasHubPermission])
def hub_team_detail(request, pk):
    hub_team_detail.required_permissions = {"GET": "cms.team.edit", "PATCH": "cms.team.edit", "DELETE": "cms.team.edit"}
    try:
        user = _hub_staff_qs().get(pk=pk)
    except HubUser.DoesNotExist:
        return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
    if request.method == "DELETE":
        user.is_deleted = True
        user.save(update_fields=["is_deleted"])
        Service.objects.filter(team_lead_id=user.id).update(team_lead_id=None)
        SubService.objects.filter(team_lead_id=user.id).update(team_lead_id=None)
        log_audit(request, "delete", "cms", f"Team member {user.name}", str(user.id), "Team member deleted")
        return Response(status=status.HTTP_204_NO_CONTENT)
    if request.method == "PATCH":
        serializer = HubStaffWriteSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        with transaction.atomic():
            if data.get("name") is not None:
                user.name = (data["name"] or "")[:255]
            if data.get("email") is not None:
                email = (data["email"] or "").strip()
                if email and email != user.email:
                    if HubUser.objects.filter(email__iexact=email, is_deleted=False).exclude(pk=user.pk).exists():
                        return Response(
                            {"detail": "Another staff member with this email already exists."},
                            status=status.HTTP_400_BAD_REQUEST,
                        )
                    user.email = email
            if data.get("password") is not None and data["password"]:
                user.set_password(data["password"])
            for attr in ("job_title", "department", "bio", "phone", "show_on_website", "sort_order", "meta_title", "meta_description", "meta_keywords"):
                if data.get(attr) is not None:
                    if attr == "show_on_website":
                        user.show_on_website = bool(data[attr])
                    elif attr == "sort_order":
                        user.sort_order = int(data[attr])
                    elif attr == "department":
                        setattr(user, attr, (data[attr] or "")[:20])
                    elif attr == "meta_description":
                        setattr(user, attr, (data[attr] or "")[:500])
                    elif attr in ("job_title", "meta_title", "meta_keywords"):
                        setattr(user, attr, (data[attr] or "")[:255])
                    else:
                        setattr(user, attr, data[attr] or "")
            if data.get("image") is not None:
                user.image = (data["image"] or "").strip() or None
                if user.image == "":
                    user.image = None
            user.save()
            if "role_ids" in data:
                user.roles.set(UserRole.objects.filter(id__in=(data["role_ids"] or [])))
            if "specializations" in data:
                user.specializations.all().delete()
                from accounts.models import UserSpecialization
                for i, text in enumerate(data["specializations"] or []):
                    if text:
                        UserSpecialization.objects.create(user=user, text=str(text)[:255], sort_order=i)
        user.refresh_from_db()
        user = _hub_staff_qs().get(pk=user.pk)
        log_audit(request, "update", "cms", f"Team member {user.name}", str(user.id), "Team member updated")
        return Response(HubStaffListSerializer(user).data)
    return Response(HubStaffListSerializer(user).data)


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated, HasHubPermission])
def hub_blog_list(request):
    hub_blog_list.required_permissions = {"GET": "cms.blog.view", "POST": "cms.blog.create"}
    from rest_framework.pagination import PageNumberPagination
    if request.method == "POST":
        serializer = BlogPostWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        post = serializer.save()
        post.refresh_from_db()
        post = BlogPost.objects.select_related("category", "author").prefetch_related("tags").get(pk=post.pk)
        log_audit(request, "create", "cms", f"Blog post {post.title}", str(post.id), "Blog post created")
        return Response(BlogPostDetailSerializer(post).data, status=status.HTTP_201_CREATED)
    qs = BlogPost.objects.filter(is_deleted=False).select_related("category").prefetch_related("tags").order_by("-published_at")
    category = request.query_params.get("category")
    if category:
        if len(category) == 36 and "-" in category:
            qs = qs.filter(category_id=category)
        else:
            qs = qs.filter(category__slug=category)
    paginator = PageNumberPagination()
    paginator.page_size = 20
    page = paginator.paginate_queryset(qs, request)
    return paginator.get_paginated_response(BlogPostListSerializer(page, many=True).data)


@api_view(["GET", "PATCH", "DELETE"])
@permission_classes([IsAuthenticated, HasHubPermission])
def hub_blog_detail(request, slug):
    hub_blog_detail.required_permissions = {"GET": "cms.blog.view", "PATCH": "cms.blog.edit", "DELETE": "cms.blog.delete"}
    try:
        post = BlogPost.objects.select_related("category", "author").prefetch_related("tags").get(slug=slug, is_deleted=False)
    except BlogPost.DoesNotExist:
        return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
    if request.method == "DELETE":
        post.is_deleted = True
        post.save()
        log_audit(request, "delete", "cms", f"Blog post {post.title}", str(post.id), "Blog post deleted")
        return Response(status=status.HTTP_204_NO_CONTENT)
    if request.method == "PATCH":
        serializer = BlogPostWriteSerializer(post, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        post = serializer.save()
        post.refresh_from_db()
        post = BlogPost.objects.select_related("category", "author").prefetch_related("tags").get(pk=post.pk)
        log_audit(request, "update", "cms", f"Blog post {post.title}", str(post.id), "Blog post updated")
        return Response(BlogPostDetailSerializer(post).data)
    return Response(BlogPostDetailSerializer(post).data)


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated, HasHubPermission])
def hub_news_list(request):
    hub_news_list.required_permissions = {"GET": "cms.news.edit", "POST": "cms.news.edit"}
    from rest_framework.pagination import PageNumberPagination
    if request.method == "POST":
        serializer = NewsItemWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        item = serializer.save()
        log_audit(request, "create", "cms", f"News item {item.title}", str(item.id), "News item created")
        return Response(NewsItemDetailSerializer(item).data, status=status.HTTP_201_CREATED)
    qs = NewsItem.objects.filter(is_deleted=False).order_by("-published_at")
    paginator = PageNumberPagination()
    paginator.page_size = 20
    page = paginator.paginate_queryset(qs, request)
    return paginator.get_paginated_response(NewsItemListSerializer(page, many=True).data)


@api_view(["GET", "PATCH", "DELETE"])
@permission_classes([IsAuthenticated, HasHubPermission])
def hub_news_detail(request, slug):
    hub_news_detail.required_permissions = {"GET": "cms.news.edit", "PATCH": "cms.news.edit", "DELETE": "cms.news.edit"}
    try:
        item = NewsItem.objects.get(slug=slug, is_deleted=False)
    except NewsItem.DoesNotExist:
        return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
    if request.method == "DELETE":
        item.is_deleted = True
        item.save()
        log_audit(request, "delete", "cms", f"News item {item.title}", str(item.id), "News item deleted")
        return Response(status=status.HTTP_204_NO_CONTENT)
    if request.method == "PATCH":
        serializer = NewsItemWriteSerializer(item, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        item = serializer.save()
        log_audit(request, "update", "cms", f"News item {item.title}", str(item.id), "News item updated")
        return Response(NewsItemDetailSerializer(item).data)
    return Response(NewsItemDetailSerializer(item).data)
