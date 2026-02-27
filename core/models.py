import uuid
from django.db import models


class SoftDeleteManager(models.Manager):
    """
    Manager that excludes is_deleted=True by default in APIs.
    - Model.objects.all() → only is_deleted=False
    - Model.objects.with_deleted() → all rows (for admin/audit)
    - Model.objects.deleted_only() → only is_deleted=True
    """

    def get_queryset(self):
        return super().get_queryset().filter(is_deleted=False)

    def with_deleted(self):
        return super().get_queryset()

    def deleted_only(self):
        return super().get_queryset().filter(is_deleted=True)


class BaseModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_deleted = models.BooleanField(default=False)

    objects = SoftDeleteManager()

    class Meta:
        abstract = True


class MarketingBaseModel(BaseModel):
    meta_title = models.CharField(max_length=255, blank=True, default="")
    meta_description = models.TextField(blank=True, default="")
    meta_keywords = models.TextField(blank=True, default="")
    focus_keyword = models.CharField(max_length=100, blank=True, null=True)
    og_title = models.CharField(max_length=255, blank=True, null=True)
    og_image = models.ImageField(upload_to="seo/og_images/", blank=True, null=True)
    slug = models.SlugField(unique=True, blank=True, null=True)
    canonical_url = models.URLField(blank=True, null=True)
    schema_markup = models.JSONField(blank=True, null=True)
    priority = models.PositiveIntegerField(default=0)

    class Meta:
        abstract = True
