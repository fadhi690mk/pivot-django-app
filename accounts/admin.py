from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import Feature, UserRole, HubUser, UserSpecialization


@admin.register(Feature)
class FeatureAdmin(admin.ModelAdmin):
    list_display = ["name", "description"]


@admin.register(UserRole)
class UserRoleAdmin(admin.ModelAdmin):
    list_display = ["name"]
    filter_horizontal = ["features"]


@admin.register(HubUser)
class HubUserAdmin(BaseUserAdmin):
    list_display = ["email", "name", "role", "is_active", "show_on_website"]
    list_filter = ["is_active", "show_on_website"]
    search_fields = ["email", "name"]
    ordering = ["email"]
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Profile", {"fields": ("name", "avatar", "role", "job_title", "department", "bio", "image", "phone", "show_on_website", "sort_order")}),
        ("Permissions", {"fields": ("is_active", "is_staff", "is_superuser", "is_deleted")}),
        ("SEO", {"fields": ("meta_title", "meta_description", "meta_keywords", "focus_keyword", "og_title", "og_image")}),
    )
    add_fieldsets = ((None, {"classes": ("wide",), "fields": ("email", "name", "password1", "password2")}),)


admin.site.register(UserSpecialization)
