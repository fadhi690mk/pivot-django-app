from django.contrib import admin
from .models import (
    HeroSlide, HeroSlideKeyService, HeroSlideStat, Client, GovernmentAgency, Testimonial, FAQ,
    Service, ServiceTargetUser, ServiceBenefit, ServiceDocument, ServiceProcessStep,
    ServicePriceTier, PriceTierFeature, ServiceFAQ, ServiceDeliverable,
    SubService, SubServiceEligibility, SubServiceBenefit, SubServiceDocument,
    SubServiceProcessStep, SubServiceProcessStepDocument, SubServiceDeliverable,
    SubServicePriceTier, SubServicePriceTierFeature, SubServiceFAQ,
    BlogPost, BlogPostTag, NewsItem,
)


# ----- Hero -----
class HeroSlideKeyServiceInline(admin.TabularInline):
    model = HeroSlideKeyService
    extra = 0


class HeroSlideStatInline(admin.TabularInline):
    model = HeroSlideStat
    extra = 0


@admin.register(HeroSlide)
class HeroSlideAdmin(admin.ModelAdmin):
    list_display = ["title", "badge", "status", "sort_order"]
    list_filter = ["status"]
    inlines = [HeroSlideKeyServiceInline, HeroSlideStatInline]


# ----- Service (parent) inlines -----
class ServiceTargetUserInline(admin.TabularInline):
    model = ServiceTargetUser
    extra = 0


class ServiceBenefitInline(admin.TabularInline):
    model = ServiceBenefit
    extra = 0


class ServiceDocumentInline(admin.TabularInline):
    model = ServiceDocument
    extra = 0


class ServiceProcessStepInline(admin.StackedInline):
    model = ServiceProcessStep
    extra = 0
    show_change_link = True


class PriceTierFeatureInline(admin.TabularInline):
    model = PriceTierFeature
    extra = 0


class ServicePriceTierInline(admin.StackedInline):
    model = ServicePriceTier
    extra = 0
    show_change_link = True


class ServiceFAQInline(admin.TabularInline):
    model = ServiceFAQ
    extra = 0


class SubServiceEligibilityInline(admin.TabularInline):
    model = SubServiceEligibility
    extra = 0


class SubServiceBenefitInline(admin.TabularInline):
    model = SubServiceBenefit
    extra = 0


class SubServiceDocumentInline(admin.TabularInline):
    model = SubServiceDocument
    extra = 0


class SubServiceProcessStepDocumentInline(admin.TabularInline):
    model = SubServiceProcessStepDocument
    extra = 0


class SubServiceProcessStepInline(admin.StackedInline):
    model = SubServiceProcessStep
    extra = 0
    show_change_link = True


class SubServiceDeliverableInline(admin.TabularInline):
    model = SubServiceDeliverable
    extra = 0


class SubServicePriceTierFeatureInline(admin.TabularInline):
    model = SubServicePriceTierFeature
    extra = 0


class SubServicePriceTierInline(admin.StackedInline):
    model = SubServicePriceTier
    extra = 0
    show_change_link = True


class SubServiceFAQInline(admin.TabularInline):
    model = SubServiceFAQ
    extra = 0


@admin.register(SubService)
class SubServiceAdmin(admin.ModelAdmin):
    inlines = [
        SubServiceEligibilityInline,
        SubServiceBenefitInline,
        SubServiceDocumentInline,
        SubServiceProcessStepInline,
        SubServiceDeliverableInline,
        SubServicePriceTierInline,
        SubServiceFAQInline,
    ]


# SubServiceProcessStep needs its own admin with document inline
class SubServiceProcessStepDocumentInlineForStep(admin.TabularInline):
    model = SubServiceProcessStepDocument
    extra = 0


@admin.register(SubServiceProcessStep)
class SubServiceProcessStepAdmin(admin.ModelAdmin):
    list_display = ["title", "sub_service", "step_number", "sort_order"]
    list_filter = ["sub_service"]
    inlines = [SubServiceProcessStepDocumentInlineForStep]


@admin.register(SubServicePriceTier)
class SubServicePriceTierAdmin(admin.ModelAdmin):
    list_display = ["name", "sub_service", "price", "is_popular", "sort_order"]
    list_filter = ["sub_service"]
    inlines = [SubServicePriceTierFeatureInline]


class ServiceDeliverableInline(admin.TabularInline):
    model = ServiceDeliverable
    extra = 0


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ["title", "slug", "status", "sort_order"]
    list_filter = ["status", "category"]
    inlines = [
        ServiceTargetUserInline,
        ServiceBenefitInline,
        ServiceDocumentInline,
        ServiceProcessStepInline,
        ServicePriceTierInline,
        ServiceFAQInline,
        ServiceDeliverableInline,
    ]


@admin.register(ServiceProcessStep)
class ServiceProcessStepAdmin(admin.ModelAdmin):
    list_display = ["title", "service", "step_number", "sort_order"]
    list_filter = ["service"]


@admin.register(ServicePriceTier)
class ServicePriceTierAdmin(admin.ModelAdmin):
    list_display = ["name", "service", "price", "is_popular", "sort_order"]
    list_filter = ["service"]
    inlines = [PriceTierFeatureInline]


# ----- Standalone / simple list -----
@admin.register(GovernmentAgency)
class GovernmentAgencyAdmin(admin.ModelAdmin):
    list_display = ["title", "subtitle", "status", "sort_order"]
    list_filter = ["status"]


# ----- Blog & News -----
class BlogPostTagInline(admin.TabularInline):
    model = BlogPostTag
    extra = 0


@admin.register(BlogPost)
class BlogPostAdmin(admin.ModelAdmin):
    list_display = ["title", "slug", "status", "published_at"]
    list_filter = ["status"]
    inlines = [BlogPostTagInline]


@admin.register(NewsItem)
class NewsItemAdmin(admin.ModelAdmin):
    list_display = ["title", "slug", "status", "published_at"]
    list_filter = ["status"]


admin.site.register(Client)
admin.site.register(Testimonial)
admin.site.register(FAQ)
