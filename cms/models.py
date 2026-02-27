import uuid
from django.db import models
from django.utils.text import slugify as _slugify
from core.models import BaseModel, MarketingBaseModel


def _make_slug_unique_global(model_class, base_slug, max_length, exclude_pk=None):
    """Return a unique slug (global uniqueness). Uses slug-2, slug-3, ... if needed."""
    base_slug = (base_slug or "").strip()[:max_length].rstrip("-")
    if not base_slug:
        base_slug = "unnamed"
    qs = model_class.objects.with_deleted()
    if exclude_pk is not None:
        qs = qs.exclude(pk=exclude_pk)
    if not qs.filter(slug=base_slug).exists():
        return base_slug
    for i in range(2, 10000):
        suffix = f"-{i}"
        candidate = (base_slug[: max_length - len(suffix)] + suffix).rstrip("-")
        if not qs.filter(slug=candidate).exists():
            return candidate
    return (base_slug[: max_length - 9] or "s") + "-" + uuid.uuid4().hex[:8]


def _make_slug_unique_per_parent(model_class, base_slug, parent_service_id, max_length, exclude_pk=None):
    """Return a unique slug per parent_service (for SubService)."""
    base_slug = (base_slug or "").strip()[:max_length].rstrip("-")
    if not base_slug:
        base_slug = "unnamed"
    qs = model_class.objects.with_deleted().filter(parent_service_id=parent_service_id)
    if exclude_pk is not None:
        qs = qs.exclude(pk=exclude_pk)
    if not qs.filter(slug=base_slug).exists():
        return base_slug
    for i in range(2, 10000):
        suffix = f"-{i}"
        candidate = (base_slug[: max_length - len(suffix)] + suffix).rstrip("-")
        if not qs.filter(slug=candidate).exists():
            return candidate
    return (base_slug[: max_length - 9] or "s") + "-" + uuid.uuid4().hex[:8]


# ----- Hero -----
class HeroSlide(MarketingBaseModel):
    """Uses inherited og_image for the hero slide image."""
    badge = models.CharField(max_length=100)
    title = models.CharField(max_length=255)
    highlight = models.CharField(max_length=255)
    subtitle = models.CharField(max_length=255, blank=True, default="")
    description = models.TextField()
    status = models.CharField(max_length=15, default="draft")
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = "cms_hero_slide"


class HeroSlideKeyService(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    hero_slide = models.ForeignKey(HeroSlide, on_delete=models.CASCADE, related_name="key_services")
    text = models.CharField(max_length=255)
    sort_order = models.PositiveIntegerField(default=0)


class HeroSlideStat(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    hero_slide = models.ForeignKey(HeroSlide, on_delete=models.CASCADE, related_name="stats")
    value = models.CharField(max_length=50)
    label = models.CharField(max_length=100)
    sort_order = models.PositiveIntegerField(default=0)


# ----- Client & Testimonial -----
class Client(MarketingBaseModel):
    title = models.CharField(max_length=255)
    logo = models.ImageField(upload_to="clients/", blank=True, null=True)
    status = models.CharField(max_length=15, default="draft")
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = "cms_client"


class GovernmentAgency(MarketingBaseModel):
    """Government agencies shown on the home page (e.g. GDRFA, DET, MOHRE)."""
    title = models.CharField(max_length=255)
    subtitle = models.CharField(max_length=255, blank=True, default="")
    logo = models.ImageField(upload_to="agencies/", blank=True, null=True)
    status = models.CharField(max_length=15, default="draft")
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = "cms_government_agency"


class Testimonial(MarketingBaseModel):
    """Uses inherited og_image for the person/featured image."""
    name = models.CharField(max_length=255)
    role = models.CharField(max_length=255, blank=True, default="")
    company = models.CharField(max_length=255, blank=True, default="")
    content = models.TextField()
    rating = models.PositiveSmallIntegerField(default=5)
    status = models.CharField(max_length=15, default="draft")
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = "cms_testimonial"


# ----- FAQ -----
class FAQ(MarketingBaseModel):
    question = models.TextField()
    answer = models.TextField()
    category = models.CharField(max_length=50, default="global")
    status = models.CharField(max_length=15, default="draft")
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = "cms_faq"


# ----- Service (parent) -----
class Service(MarketingBaseModel):
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=100, unique=True, blank=True)
    short_title = models.CharField(max_length=100, blank=True, default="")
    tagline = models.CharField(max_length=255, blank=True, default="")
    description = models.TextField(blank=True, default="")
    long_description = models.TextField(blank=True, default="")
    hero_image = models.ImageField(upload_to="services/", blank=True, null=True)
    category = models.CharField(max_length=20, default="general")
    starting_price = models.CharField(max_length=50, blank=True, default="")
    offer_badge = models.CharField(max_length=100, blank=True, default="")
    timeline = models.CharField(max_length=100, blank=True, default="")
    team_lead = models.ForeignKey(
        "accounts.HubUser", null=True, blank=True, on_delete=models.SET_NULL, related_name="led_services"
    )
    status = models.CharField(max_length=15, default="draft")
    sort_order = models.PositiveIntegerField(default=0)
    related_services = models.ManyToManyField("self", blank=True, symmetrical=False)
    # Lucide icon name for frontend (e.g. Building2, Plane, FileText)
    icon = models.CharField(max_length=64, blank=True, default="")

    class Meta:
        db_table = "cms_service"

    def save(self, *args, **kwargs):
        regenerate = not (self.slug or "").strip()
        if self.pk:
            try:
                old = Service.objects.with_deleted().filter(pk=self.pk).values_list("title", flat=True).first()
                if old is not None and old != self.title:
                    regenerate = True
            except Exception:
                pass
        if regenerate and (self.title or "").strip():
            base = _slugify(self.title).strip() or "unnamed"
            self.slug = _make_slug_unique_global(Service, base, 100, exclude_pk=self.pk)
        elif not (self.slug or "").strip() and (self.title or "").strip():
            base = _slugify(self.title).strip() or "unnamed"
            self.slug = _make_slug_unique_global(Service, base, 100, exclude_pk=self.pk)
        super().save(*args, **kwargs)

    @property
    def expert(self):
        """The user who is the expert for this service (same as team_lead)."""
        return self.team_lead


class ServiceTargetUser(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name="target_users")
    text = models.CharField(max_length=255)
    sort_order = models.PositiveIntegerField(default=0)


class ServiceBenefit(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name="benefits")
    text = models.CharField(max_length=500)
    sort_order = models.PositiveIntegerField(default=0)


class ServiceDocument(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name="required_documents")
    text = models.CharField(max_length=500)
    sort_order = models.PositiveIntegerField(default=0)


class ServiceProcessStep(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name="process_steps")
    step_number = models.PositiveSmallIntegerField(default=1)
    title = models.CharField(max_length=255)
    description = models.TextField()
    timeline = models.CharField(max_length=100, blank=True, null=True)
    sort_order = models.PositiveIntegerField(default=0)


class ServicePriceTier(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name="price_tiers")
    name = models.CharField(max_length=100)
    price = models.CharField(max_length=50)
    description = models.CharField(max_length=255, blank=True, null=True)
    is_popular = models.BooleanField(default=False)
    sort_order = models.PositiveIntegerField(default=0)


class PriceTierFeature(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    price_tier = models.ForeignKey(ServicePriceTier, on_delete=models.CASCADE, related_name="features")
    text = models.CharField(max_length=500)
    sort_order = models.PositiveIntegerField(default=0)


class ServiceFAQ(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name="faqs")
    question = models.TextField()
    answer = models.TextField()
    sort_order = models.PositiveIntegerField(default=0)


class ServiceDeliverable(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name="deliverables")
    text = models.CharField(max_length=500)
    sort_order = models.PositiveIntegerField(default=0)


# ----- SubService -----
class SubService(MarketingBaseModel):
    parent_service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name="sub_services")
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=100, blank=True)
    tagline = models.CharField(max_length=255, blank=True, default="")
    description = models.TextField(blank=True, default="")
    long_description = models.TextField(blank=True, default="")
    hero_image = models.ImageField(upload_to="subservices/", blank=True, null=True)
    starting_price = models.CharField(max_length=50, blank=True, default="")
    offer_badge = models.CharField(max_length=100, blank=True, default="")
    timeline = models.CharField(max_length=100, blank=True, default="")
    team_lead = models.ForeignKey(
        "accounts.HubUser", null=True, blank=True, on_delete=models.SET_NULL, related_name="led_subservices"
    )
    status = models.CharField(max_length=15, default="draft")
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = "cms_sub_service"
        unique_together = [["parent_service", "slug"]]

    def save(self, *args, **kwargs):
        regenerate = not (self.slug or "").strip()
        if self.pk and self.parent_service_id:
            try:
                old = SubService.objects.with_deleted().filter(pk=self.pk).values_list("title", flat=True).first()
                if old is not None and old != self.title:
                    regenerate = True
            except Exception:
                pass
        if regenerate and (self.title or "").strip() and self.parent_service_id:
            base = _slugify(self.title).strip() or "unnamed"
            self.slug = _make_slug_unique_per_parent(
                SubService, base, self.parent_service_id, 100, exclude_pk=self.pk
            )
        elif not (self.slug or "").strip() and (self.title or "").strip() and self.parent_service_id:
            base = _slugify(self.title).strip() or "unnamed"
            self.slug = _make_slug_unique_per_parent(
                SubService, base, self.parent_service_id, 100, exclude_pk=self.pk
            )
        super().save(*args, **kwargs)


class SubServiceEligibility(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    sub_service = models.ForeignKey(SubService, on_delete=models.CASCADE, related_name="eligibility")
    text = models.CharField(max_length=500)
    sort_order = models.PositiveIntegerField(default=0)


class SubServiceBenefit(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    sub_service = models.ForeignKey(SubService, on_delete=models.CASCADE, related_name="benefits")
    text = models.CharField(max_length=500)
    sort_order = models.PositiveIntegerField(default=0)


class SubServiceDocument(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    sub_service = models.ForeignKey(SubService, on_delete=models.CASCADE, related_name="required_documents")
    text = models.CharField(max_length=500)
    sort_order = models.PositiveIntegerField(default=0)


class SubServiceProcessStep(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    sub_service = models.ForeignKey(SubService, on_delete=models.CASCADE, related_name="process_steps")
    step_number = models.PositiveSmallIntegerField(default=1)
    title = models.CharField(max_length=255)
    description = models.TextField()
    timeline = models.CharField(max_length=100, blank=True, null=True)
    sort_order = models.PositiveIntegerField(default=0)


class SubServiceProcessStepDocument(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    process_step = models.ForeignKey(
        SubServiceProcessStep, on_delete=models.CASCADE, related_name="documents"
    )
    text = models.CharField(max_length=500)
    sort_order = models.PositiveIntegerField(default=0)


class SubServiceDeliverable(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    sub_service = models.ForeignKey(SubService, on_delete=models.CASCADE, related_name="deliverables")
    text = models.CharField(max_length=500)
    sort_order = models.PositiveIntegerField(default=0)


class SubServicePriceTier(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    sub_service = models.ForeignKey(SubService, on_delete=models.CASCADE, related_name="price_tiers")
    name = models.CharField(max_length=100)
    price = models.CharField(max_length=50)
    description = models.CharField(max_length=255, blank=True, null=True)
    is_popular = models.BooleanField(default=False)
    sort_order = models.PositiveIntegerField(default=0)


class SubServicePriceTierFeature(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    price_tier = models.ForeignKey(
        SubServicePriceTier, on_delete=models.CASCADE, related_name="features"
    )
    text = models.CharField(max_length=500)
    sort_order = models.PositiveIntegerField(default=0)


class SubServiceFAQ(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    sub_service = models.ForeignKey(SubService, on_delete=models.CASCADE, related_name="faqs")
    question = models.TextField()
    answer = models.TextField()
    sort_order = models.PositiveIntegerField(default=0)


# ----- Blog & News -----
class BlogPost(MarketingBaseModel):
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True, blank=True)
    category = models.ForeignKey(
        Service,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="blog_posts",
    )
    author = models.ForeignKey(
        "accounts.HubUser",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="blog_posts",
    )
    author_name = models.CharField(max_length=255, blank=True, default="")
    status = models.CharField(max_length=15, default="published")
    published_at = models.DateTimeField(blank=True, null=True)
    views = models.PositiveIntegerField(default=0)
    excerpt = models.TextField()
    content = models.TextField()
    read_time = models.CharField(max_length=20, blank=True, default="")
    # Uses inherited og_image for featured image.

    class Meta:
        db_table = "cms_blog_post"

    def save(self, *args, **kwargs):
        regenerate = not (self.slug or "").strip()
        if self.pk:
            try:
                old = BlogPost.objects.with_deleted().filter(pk=self.pk).values_list("title", flat=True).first()
                if old is not None and old != self.title:
                    regenerate = True
            except Exception:
                pass
        if regenerate and (self.title or "").strip():
            base = _slugify(self.title).strip() or "unnamed"
            self.slug = _make_slug_unique_global(BlogPost, base, 255, exclude_pk=self.pk)
        elif not (self.slug or "").strip() and (self.title or "").strip():
            base = _slugify(self.title).strip() or "unnamed"
            self.slug = _make_slug_unique_global(BlogPost, base, 255, exclude_pk=self.pk)
        super().save(*args, **kwargs)


class BlogPostTag(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    blog_post = models.ForeignKey(BlogPost, on_delete=models.CASCADE, related_name="tags")
    name = models.CharField(max_length=100)


class NewsItem(MarketingBaseModel):
    """Uses inherited og_image for featured image."""
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True, blank=True)
    excerpt = models.TextField()
    content = models.TextField()
    category = models.ForeignKey(
        Service,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="news_items",
    )
    source = models.CharField(max_length=255, blank=True, default="")
    status = models.CharField(max_length=15, default="published")
    published_at = models.DateField(blank=True, null=True)

    class Meta:
        db_table = "cms_news_item"

    def save(self, *args, **kwargs):
        regenerate = not (self.slug or "").strip()
        if self.pk:
            try:
                old = NewsItem.objects.with_deleted().filter(pk=self.pk).values_list("title", flat=True).first()
                if old is not None and old != self.title:
                    regenerate = True
            except Exception:
                pass
        if regenerate and (self.title or "").strip():
            base = _slugify(self.title).strip() or "unnamed"
            self.slug = _make_slug_unique_global(NewsItem, base, 255, exclude_pk=self.pk)
        elif not (self.slug or "").strip() and (self.title or "").strip():
            base = _slugify(self.title).strip() or "unnamed"
            self.slug = _make_slug_unique_global(NewsItem, base, 255, exclude_pk=self.pk)
        super().save(*args, **kwargs)


