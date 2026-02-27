import uuid
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from core.models import BaseModel


FEATURES_CHOICES = [
    ("leads.view", "View Leads"),
    ("leads.create", "Create Leads"),
    ("leads.edit", "Edit Leads"),
    ("leads.delete", "Delete Leads"),
    ("leads.assign", "Assign Leads"),
    ("cms.blog.view", "View Blog"),
    ("cms.blog.create", "Create Blog"),
    ("cms.blog.edit", "Edit Blog"),
    ("cms.blog.publish", "Publish Blog"),
    ("cms.blog.delete", "Delete Blog"),
    ("cms.services.view", "View Services"),
    ("cms.services.edit", "Edit Services"),
    ("cms.services.publish", "Publish Services"),
    ("cms.hero.edit", "Edit Hero"),
    ("cms.team.edit", "Edit Team"),
    ("cms.clients.edit", "Edit Clients"),
    ("cms.testimonials.edit", "Edit Testimonials"),
    ("cms.news.edit", "Edit News"),
    ("cms.faq.edit", "Edit FAQs"),
    ("cms.pages.edit", "Edit Pages"),
    ("config.calculator", "Manage Calculator"),
    ("config.search", "Manage Search"),
    ("config.roles", "Manage Roles"),
    ("invoices.view", "View Invoices"),
    ("invoices.create", "Create Invoices"),
    ("invoices.edit", "Edit Invoices"),
    ("invoices.delete", "Delete Invoices"),
    ("audit.view", "View Audit Log"),
    ("settings.manage", "Manage Settings"),
]


class Feature(BaseModel):
    name = models.CharField(max_length=150, unique=True, choices=FEATURES_CHOICES)
    description = models.TextField(blank=True, default="")

    class Meta:
        db_table = "accounts_feature"

    def __str__(self):
        return self.name


class UserRole(BaseModel):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, default="")
    features = models.ManyToManyField(Feature, related_name="roles", blank=True)

    class Meta:
        db_table = "accounts_user_role"

    def __str__(self):
        return self.name


class HubUserManager(BaseUserManager):
    def create_user(self, email, name, password=None, **kwargs):
        if not email:
            raise ValueError("Email required")
        user = self.model(email=self.normalize_email(email), name=name, **kwargs)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, name, password=None, **kwargs):
        kwargs.setdefault("is_staff", True)
        kwargs.setdefault("is_superuser", True)
        return self.create_user(email, name, password=password, **kwargs)


class HubUser(AbstractBaseUser, PermissionsMixin):
    """
    Staff/team member. When show_on_website=True, included in public GET /api/cms/team/
    and shown on the public /team page. Fields used on team page: name, job_title (role),
    department, bio, image, email, phone, specializations (UserSpecialization),
    led_services (Service.team_lead → linkedServices).
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    name = models.CharField(max_length=255)
    avatar = models.CharField(max_length=10, blank=True, default="")
    role = models.ForeignKey(UserRole, null=True, blank=True, on_delete=models.SET_NULL, related_name="users")
    roles = models.ManyToManyField(UserRole, related_name="hub_users", blank=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    job_title = models.CharField(max_length=255, blank=True, default="")
    department = models.CharField(max_length=20, blank=True, default="")
    bio = models.TextField(blank=True, default="")
    image = models.ImageField(upload_to="team/", blank=True, null=True)
    phone = models.CharField(max_length=30, blank=True, default="")
    show_on_website = models.BooleanField(default=False, help_text="When True, show on public /team page")
    sort_order = models.PositiveIntegerField(default=0)

    meta_title = models.CharField(max_length=255, blank=True, default="")
    meta_description = models.TextField(blank=True, default="")
    meta_keywords = models.TextField(blank=True, default="")
    focus_keyword = models.CharField(max_length=100, blank=True, null=True)
    og_title = models.CharField(max_length=255, blank=True, null=True)
    og_image = models.ImageField(upload_to="seo/og_images/", blank=True, null=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["name"]
    objects = HubUserManager()

    class Meta:
        db_table = "accounts_hub_user"

    def __str__(self):
        return self.email

    def get_permission_names(self):
        """Return set of feature names (permissions) from role FK and roles M2M."""
        names = set()
        if self.role_id:
            names.update(
                self.role.features.filter(is_deleted=False).values_list("name", flat=True)
            )
        names.update(
            Feature.objects.filter(roles__hub_users=self, is_deleted=False).values_list(
                "name", flat=True
            )
        )
        return names


class UserSpecialization(BaseModel):
    user = models.ForeignKey(HubUser, on_delete=models.CASCADE, related_name="specializations")
    text = models.CharField(max_length=255)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = "accounts_user_specialization"


