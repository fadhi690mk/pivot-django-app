from rest_framework import serializers
from .models import (
    HeroSlide, Client, GovernmentAgency, Testimonial, FAQ, Service, ServiceBenefit, ServiceDocument,
    ServiceProcessStep, ServicePriceTier, PriceTierFeature, ServiceFAQ, ServiceTargetUser,
    ServiceDeliverable,
    SubService, SubServiceProcessStep, SubServiceProcessStepDocument,
    SubServicePriceTier, SubServicePriceTierFeature, SubServiceFAQ,
    BlogPost, BlogPostTag, NewsItem,
)
from accounts.serializers import UserRoleSerializer
from accounts.models import HubUser, UserRole


def normalize_media_path(path):
    """Ensure path is relative to MEDIA_ROOT (no leading / or media/). Prevents /media/media/... 404s."""
    if not path or not isinstance(path, str):
        return path
    s = path.strip().lstrip("/")
    if s.lower().startswith("media/"):
        s = s[6:].lstrip("/")
    return s or None


class HeroSlideSerializer(serializers.ModelSerializer):
    image = serializers.ImageField(source="og_image", read_only=True)
    key_services = serializers.SerializerMethodField()
    stats = serializers.SerializerMethodField()

    class Meta:
        model = HeroSlide
        fields = ["id", "badge", "title", "highlight", "subtitle", "description", "image", "key_services", "stats", "status", "sort_order"]

    def get_key_services(self, obj):
        return [s.text for s in obj.key_services.order_by("sort_order")]

    def get_stats(self, obj):
        return [{"value": s.value, "label": s.label} for s in obj.stats.order_by("sort_order")]


class HeroSlideWriteSerializer(serializers.ModelSerializer):
    key_services = serializers.ListField(child=serializers.CharField(max_length=255), required=False, default=list)
    stats = serializers.ListField(
        child=serializers.DictField(child=serializers.CharField()),
        required=False,
        default=list,
    )
    image_path = serializers.CharField(required=False, allow_blank=True, write_only=True)

    class Meta:
        model = HeroSlide
        fields = ["badge", "title", "highlight", "subtitle", "description", "key_services", "stats", "status", "sort_order", "image_path"]

    def create(self, validated_data):
        from .models import HeroSlideKeyService, HeroSlideStat
        image_path = validated_data.pop("image_path", "").strip()
        key_services = validated_data.pop("key_services", [])
        stats = validated_data.pop("stats", [])
        slide = HeroSlide.objects.create(**validated_data)
        if image_path:
            slide.og_image = normalize_media_path(image_path)
            slide.save(update_fields=["og_image"])
        for i, text in enumerate(key_services):
            HeroSlideKeyService.objects.create(hero_slide=slide, text=text, sort_order=i)
        for i, item in enumerate(stats):
            HeroSlideStat.objects.create(
                hero_slide=slide,
                value=item.get("value", ""),
                label=item.get("label", ""),
                sort_order=i,
            )
        return slide

    def update(self, instance, validated_data):
        from .models import HeroSlideKeyService, HeroSlideStat
        image_path = validated_data.pop("image_path", "").strip()
        key_services = validated_data.pop("key_services", None)
        stats = validated_data.pop("stats", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if image_path:
            instance.og_image = normalize_media_path(image_path)
        instance.save()
        if key_services is not None:
            instance.key_services.all().delete()
            for i, text in enumerate(key_services):
                HeroSlideKeyService.objects.create(hero_slide=instance, text=text, sort_order=i)
        if stats is not None:
            instance.stats.all().delete()
            for i, item in enumerate(stats):
                HeroSlideStat.objects.create(
                    hero_slide=instance,
                    value=item.get("value", ""),
                    label=item.get("label", ""),
                    sort_order=i,
                )
        return instance


class ClientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Client
        fields = ["id", "title", "logo", "status", "sort_order"]


class GovernmentAgencySerializer(serializers.ModelSerializer):
    class Meta:
        model = GovernmentAgency
        fields = ["id", "title", "subtitle", "logo", "status", "sort_order"]


class GovernmentAgencyWriteSerializer(serializers.ModelSerializer):
    logo_path = serializers.CharField(required=False, allow_blank=True, write_only=True)

    class Meta:
        model = GovernmentAgency
        fields = ["title", "subtitle", "logo_path", "status", "sort_order"]

    def create(self, validated_data):
        logo_path = validated_data.pop("logo_path", "").strip()
        agency = GovernmentAgency.objects.create(**validated_data)
        if logo_path:
            agency.logo = normalize_media_path(logo_path)
            agency.save(update_fields=["logo"])
        return agency

    def update(self, instance, validated_data):
        logo_path = validated_data.pop("logo_path", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if logo_path is not None:
            instance.logo = (normalize_media_path(logo_path.strip()) or None) if logo_path.strip() else None
        instance.save()
        return instance


class ClientWriteSerializer(serializers.ModelSerializer):
    logo_path = serializers.CharField(required=False, allow_blank=True, write_only=True)

    class Meta:
        model = Client
        fields = ["title", "logo_path", "status", "sort_order"]

    def create(self, validated_data):
        logo_path = validated_data.pop("logo_path", "").strip()
        client = Client.objects.create(**validated_data)
        if logo_path:
            client.logo = normalize_media_path(logo_path)
            client.save(update_fields=["logo"])
        return client

    def update(self, instance, validated_data):
        logo_path = validated_data.pop("logo_path", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if logo_path is not None:
            instance.logo = (normalize_media_path(logo_path.strip()) or None) if logo_path.strip() else None
        instance.save()
        return instance


class TestimonialSerializer(serializers.ModelSerializer):
    image = serializers.ImageField(source="og_image", read_only=True)

    class Meta:
        model = Testimonial
        fields = ["id", "name", "role", "company", "content", "rating", "image", "status", "sort_order"]


class TestimonialWriteSerializer(serializers.ModelSerializer):
    image_path = serializers.CharField(required=False, allow_blank=True, write_only=True)

    class Meta:
        model = Testimonial
        fields = ["name", "role", "company", "content", "rating", "image_path", "status", "sort_order"]

    def create(self, validated_data):
        image_path = validated_data.pop("image_path", "").strip()
        testimonial = Testimonial.objects.create(**validated_data)
        if image_path:
            testimonial.og_image = normalize_media_path(image_path)
            testimonial.save(update_fields=["og_image"])
        return testimonial

    def update(self, instance, validated_data):
        image_path = validated_data.pop("image_path", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if image_path is not None:
            instance.og_image = (normalize_media_path(image_path.strip()) or None) if image_path.strip() else None
        instance.save()
        return instance


class FAQSerializer(serializers.ModelSerializer):
    class Meta:
        model = FAQ
        fields = ["id", "question", "answer", "category", "status", "sort_order"]


class FAQWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = FAQ
        fields = ["question", "answer", "category", "status", "sort_order"]


# ----- Service (nested) -----
class ServiceTargetUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = ServiceTargetUser
        fields = ["id", "text", "sort_order"]


class ServiceBenefitSerializer(serializers.ModelSerializer):
    class Meta:
        model = ServiceBenefit
        fields = ["id", "text", "sort_order"]


class ServiceDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = ServiceDocument
        fields = ["id", "text", "sort_order"]


class ServiceProcessStepSerializer(serializers.ModelSerializer):
    step = serializers.IntegerField(source="step_number", read_only=True)

    class Meta:
        model = ServiceProcessStep
        fields = ["id", "step", "step_number", "title", "description", "timeline", "sort_order"]


class PriceTierFeatureSerializer(serializers.ModelSerializer):
    class Meta:
        model = PriceTierFeature
        fields = ["id", "text", "sort_order"]


class ServicePriceTierSerializer(serializers.ModelSerializer):
    features = PriceTierFeatureSerializer(many=True, read_only=True)
    popular = serializers.BooleanField(source="is_popular", read_only=True)

    class Meta:
        model = ServicePriceTier
        fields = ["id", "name", "price", "description", "features", "popular", "is_popular", "sort_order"]


class ServiceFAQSerializer(serializers.ModelSerializer):
    class Meta:
        model = ServiceFAQ
        fields = ["id", "question", "answer", "sort_order"]


class TeamLeadSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    name = serializers.CharField()
    role = serializers.CharField(source="job_title")
    image = serializers.ImageField(allow_null=True)
    email = serializers.EmailField()
    phone = serializers.CharField(allow_blank=True, default="")


class HubStaffListSerializer(serializers.Serializer):
    """Read-only list/detail of a hub staff member for Hub API."""
    id = serializers.UUIDField()
    name = serializers.CharField()
    email = serializers.EmailField()
    role = serializers.CharField(source="job_title", default="")
    job_title = serializers.CharField()
    department = serializers.CharField()
    bio = serializers.CharField()
    image = serializers.SerializerMethodField()
    phone = serializers.CharField()
    show_on_website = serializers.BooleanField()
    sort_order = serializers.IntegerField()
    meta_title = serializers.CharField(allow_blank=True, default="")
    meta_description = serializers.CharField(allow_blank=True, default="")
    meta_keywords = serializers.CharField(allow_blank=True, default="")
    roles = serializers.SerializerMethodField()
    specializations = serializers.SerializerMethodField()
    linkedServices = serializers.SerializerMethodField()
    linkedSubservices = serializers.SerializerMethodField()

    def get_image(self, obj):
        if obj.image:
            try:
                return obj.image.url
            except Exception:
                return None
        return None

    def get_roles(self, obj):
        return [{"id": str(r.id), "name": r.name} for r in (getattr(obj, "roles_prefetched", None) or obj.roles.all())]

    def get_specializations(self, obj):
        return list(obj.specializations.order_by("sort_order").values_list("text", flat=True))

    def get_linkedServices(self, obj):
        return [s.slug for s in obj.led_services.all()]

    def get_linkedSubservices(self, obj):
        return [f"{s.parent_service.slug}/{s.slug}" for s in obj.led_subservices.select_related("parent_service").all()]


class HubStaffWriteSerializer(serializers.Serializer):
    """Create/update hub staff. Accepts role_ids and linked_services (service slugs)."""
    name = serializers.CharField(max_length=255)
    email = serializers.EmailField(required=False, allow_blank=False)
    password = serializers.CharField(required=False, allow_blank=True, write_only=True)
    job_title = serializers.CharField(max_length=255, required=False, allow_blank=True, default="")
    department = serializers.CharField(max_length=20, required=False, allow_blank=True, default="")
    bio = serializers.CharField(required=False, allow_blank=True, default="")
    phone = serializers.CharField(max_length=30, required=False, allow_blank=True, default="")
    image = serializers.CharField(required=False, allow_blank=True, default="")
    show_on_website = serializers.BooleanField(required=False, default=False)
    sort_order = serializers.IntegerField(required=False, default=0)
    meta_title = serializers.CharField(required=False, allow_blank=True, max_length=255, default="")
    meta_description = serializers.CharField(required=False, allow_blank=True, default="")
    meta_keywords = serializers.CharField(required=False, allow_blank=True, max_length=255, default="")
    role_ids = serializers.ListField(child=serializers.UUIDField(), required=False, default=list)
    linked_services = serializers.ListField(child=serializers.SlugField(), required=False, default=list)
    specializations = serializers.ListField(child=serializers.CharField(max_length=255), required=False, default=list)


class ServiceListSerializer(serializers.ModelSerializer):
    sub_services_count = serializers.SerializerMethodField()
    sub_services = serializers.SerializerMethodField()

    class Meta:
        model = Service
        fields = [
            "id", "title", "slug", "short_title", "tagline", "description", "category",
            "starting_price", "offer_badge", "hero_image", "icon", "status", "sort_order", "sub_services_count", "sub_services",
        ]

    def get_sub_services_count(self, obj):
        return obj.sub_services.filter(is_deleted=False).count()

    def get_sub_services(self, obj):
        """First 4 sub-services for list/card display (e.g. services page)."""
        ordered = list(obj.sub_services.all())[:4]
        return [{"id": str(s.id), "title": s.title, "slug": s.slug} for s in ordered]


class ServiceDetailSerializer(serializers.ModelSerializer):
    benefits = ServiceBenefitSerializer(many=True, read_only=True)
    required_documents = ServiceDocumentSerializer(many=True, read_only=True)
    process_steps = ServiceProcessStepSerializer(many=True, read_only=True)
    price_tiers = ServicePriceTierSerializer(many=True, read_only=True)
    faqs = ServiceFAQSerializer(many=True, read_only=True)
    target_users = serializers.SerializerMethodField()
    deliverables = serializers.SerializerMethodField()
    team_lead = TeamLeadSerializer(read_only=True)
    related_services = ServiceListSerializer(many=True, read_only=True)
    sub_services = serializers.SerializerMethodField()

    class Meta:
        model = Service
        fields = [
            "id", "title", "slug", "short_title", "tagline", "description", "long_description",
            "hero_image", "category", "starting_price", "offer_badge", "timeline", "sort_order", "icon",
            "target_users", "benefits", "required_documents", "process_steps", "deliverables",
            "price_tiers", "faqs", "team_lead", "related_services", "sub_services",
            "meta_title", "meta_description", "meta_keywords",
        ]

    def get_target_users(self, obj):
        return [s.text for s in obj.target_users.order_by("sort_order")]

    def get_deliverables(self, obj):
        return list(obj.deliverables.order_by("sort_order").values_list("text", flat=True))

    def get_sub_services(self, obj):
        return [
            {"id": str(s.id), "title": s.title, "slug": s.slug, "starting_price": s.starting_price, "description": s.description}
            for s in obj.sub_services.filter(is_deleted=False).order_by("sort_order")
        ]


class SubServiceListSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubService
        fields = ["id", "title", "slug", "starting_price", "description", "tagline", "sort_order"]


# ----- SubService detail (full page) -----
class SubServiceProcessStepDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubServiceProcessStepDocument
        fields = ["id", "text", "sort_order"]


class SubServiceProcessStepSerializer(serializers.ModelSerializer):
    documents = serializers.SerializerMethodField()

    class Meta:
        model = SubServiceProcessStep
        fields = ["id", "step_number", "title", "description", "timeline", "sort_order", "documents"]

    def get_documents(self, obj):
        return list(obj.documents.order_by("sort_order").values_list("text", flat=True))


class SubServicePriceTierFeatureSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubServicePriceTierFeature
        fields = ["id", "text", "sort_order"]


class SubServicePriceTierSerializer(serializers.ModelSerializer):
    features = SubServicePriceTierFeatureSerializer(many=True, read_only=True)
    popular = serializers.BooleanField(source="is_popular", read_only=True)

    class Meta:
        model = SubServicePriceTier
        fields = ["id", "name", "price", "description", "features", "popular", "is_popular", "sort_order"]


class SubServiceFAQSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubServiceFAQ
        fields = ["id", "question", "answer", "sort_order"]


class SubServiceDetailSerializer(serializers.ModelSerializer):
    parent_slug = serializers.CharField(source="parent_service.slug", read_only=True)
    eligibility = serializers.SerializerMethodField()
    benefits = serializers.SerializerMethodField()
    required_documents = serializers.SerializerMethodField()
    process_steps = SubServiceProcessStepSerializer(many=True, read_only=True)
    deliverables = serializers.SerializerMethodField()
    price_tiers = SubServicePriceTierSerializer(many=True, read_only=True)
    faqs = SubServiceFAQSerializer(many=True, read_only=True)
    team_lead = TeamLeadSerializer(read_only=True)
    meta_title = serializers.CharField(read_only=True)
    meta_description = serializers.CharField(read_only=True)
    meta_keywords = serializers.CharField(read_only=True)

    class Meta:
        model = SubService
        fields = [
            "id", "title", "slug", "parent_slug", "tagline", "description", "long_description",
            "hero_image", "starting_price", "offer_badge", "timeline", "sort_order",
            "eligibility", "benefits", "required_documents", "process_steps", "deliverables",
            "price_tiers", "faqs", "team_lead",
            "meta_title", "meta_description", "meta_keywords",
        ]

    def get_eligibility(self, obj):
        return list(obj.eligibility.order_by("sort_order").values_list("text", flat=True))

    def get_benefits(self, obj):
        return list(obj.benefits.order_by("sort_order").values_list("text", flat=True))

    def get_required_documents(self, obj):
        return list(obj.required_documents.order_by("sort_order").values_list("text", flat=True))

    def get_deliverables(self, obj):
        return list(obj.deliverables.order_by("sort_order").values_list("text", flat=True))


# ----- Blog -----
class BlogPostCategorySerializer(serializers.Serializer):
    id = serializers.UUIDField(read_only=True)
    title = serializers.CharField(read_only=True)
    slug = serializers.SlugField(read_only=True)


def _blog_read_time(obj):
    """Return stored read_time if set, else compute from content (~200 words/min)."""
    if getattr(obj, "read_time", None) and str(obj.read_time).strip():
        return str(obj.read_time).strip()
    content = getattr(obj, "content", None) or ""
    text = (content if isinstance(content, str) else "").replace("<", " ").replace(">", " ")
    words = len(text.split())
    min_ = max(1, (words + 199) // 200)
    return f"{min_} min read"


class BlogPostListSerializer(serializers.ModelSerializer):
    image = serializers.ImageField(source="og_image", read_only=True)
    author_name = serializers.CharField(read_only=True)
    tags = serializers.SerializerMethodField()
    category = BlogPostCategorySerializer(read_only=True)
    read_time = serializers.SerializerMethodField()

    class Meta:
        model = BlogPost
        fields = ["id", "title", "slug", "category", "author_name", "status", "published_at", "views", "excerpt", "image", "tags", "read_time"]

    def get_tags(self, obj):
        return list(obj.tags.values_list("name", flat=True))

    def get_read_time(self, obj):
        return _blog_read_time(obj)


class BlogPostDetailSerializer(serializers.ModelSerializer):
    image = serializers.ImageField(source="og_image", read_only=True)
    tags = serializers.SerializerMethodField()
    category = BlogPostCategorySerializer(read_only=True)
    read_time = serializers.SerializerMethodField()

    class Meta:
        model = BlogPost
        fields = ["id", "title", "slug", "category", "author_name", "published_at", "views", "excerpt", "content", "image", "tags", "read_time", "meta_title", "meta_description"]

    def get_tags(self, obj):
        return list(obj.tags.values_list("name", flat=True))

    def get_read_time(self, obj):
        return _blog_read_time(obj)


# ----- News -----
class NewsItemListSerializer(serializers.ModelSerializer):
    image = serializers.ImageField(source="og_image", read_only=True)
    category = BlogPostCategorySerializer(read_only=True)

    class Meta:
        model = NewsItem
        fields = ["id", "title", "slug", "category", "excerpt", "image", "source", "published_at", "status"]


class NewsItemDetailSerializer(serializers.ModelSerializer):
    image = serializers.ImageField(source="og_image", read_only=True)
    category = BlogPostCategorySerializer(read_only=True)

    class Meta:
        model = NewsItem
        fields = ["id", "title", "slug", "category", "excerpt", "content", "image", "source", "published_at", "status", "meta_title", "meta_description"]


# ----- Blog Write -----
class BlogPostWriteSerializer(serializers.ModelSerializer):
    category = serializers.PrimaryKeyRelatedField(queryset=Service.objects.filter(is_deleted=False), required=False, allow_null=True)
    tags = serializers.ListField(child=serializers.CharField(max_length=100), required=False, default=list)
    image_path = serializers.CharField(required=False, allow_blank=True, write_only=True)
    published_at = serializers.DateTimeField(required=False, allow_null=True)
    read_time = serializers.CharField(required=False, allow_blank=True, max_length=20)

    class Meta:
        model = BlogPost
        fields = [
            "title", "category", "author_name", "status", "published_at",
            "excerpt", "content", "read_time", "image_path", "tags",
            "meta_title", "meta_description",
        ]

    def create(self, validated_data):
        tags = validated_data.pop("tags", [])
        image_path = validated_data.pop("image_path", "").strip()
        post = BlogPost.objects.create(**validated_data)
        if image_path:
            post.og_image = normalize_media_path(image_path)
            post.save(update_fields=["og_image"])
        for name in tags:
            if name:
                BlogPostTag.objects.create(blog_post=post, name=str(name)[:100])
        return post

    def update(self, instance, validated_data):
        tags = validated_data.pop("tags", None)
        image_path = validated_data.pop("image_path", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if image_path is not None:
            instance.og_image = (normalize_media_path(image_path.strip()) or None) if image_path.strip() else None
        instance.save()
        if tags is not None:
            instance.tags.all().delete()
            for name in tags:
                if name:
                    BlogPostTag.objects.create(blog_post=instance, name=str(name)[:100])
        return instance


# ----- News Write -----
class NewsItemWriteSerializer(serializers.ModelSerializer):
    category = serializers.PrimaryKeyRelatedField(queryset=Service.objects.filter(is_deleted=False), required=False, allow_null=True)
    image_path = serializers.CharField(required=False, allow_blank=True, write_only=True)
    published_at = serializers.DateField(required=False, allow_null=True)

    class Meta:
        model = NewsItem
        fields = [
            "title", "excerpt", "content", "category", "source", "status",
            "published_at", "image_path", "meta_title", "meta_description",
        ]

    def create(self, validated_data):
        image_path = validated_data.pop("image_path", "").strip()
        item = NewsItem.objects.create(**validated_data)
        if image_path:
            item.og_image = normalize_media_path(image_path)
            item.save(update_fields=["og_image"])
        return item

    def update(self, instance, validated_data):
        image_path = validated_data.pop("image_path", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if image_path is not None:
            instance.og_image = (normalize_media_path(image_path.strip()) or None) if image_path.strip() else None
        instance.save()
        return instance
