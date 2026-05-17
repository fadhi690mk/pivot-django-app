from django.core.management.base import BaseCommand
from accounts.models import Feature, UserRole, HubUser
from accounts.models import FEATURES_CHOICES


# Mock roles aligned with Hub frontend (mockHubData.ts)
MOCK_ROLES = [
    ("Admin", "Full access to all features", None),  # None = all features
    ("Sales Manager", "Lead management and pipeline access", [
        "leads.view", "leads.create", "leads.edit", "leads.assign",
        "cms.blog.view", "invoices.view", "invoices.create",
    ]),
    ("Sales Rep", "View and manage assigned leads", [
        "leads.view", "leads.create", "leads.edit", "invoices.view",
    ]),
    ("Content Editor", "Manage blog, news, and content", [
        "cms.blog.view", "cms.blog.create", "cms.blog.edit", "cms.blog.publish",
        "cms.news.edit", "cms.faq.edit",
    ]),
    ("Viewer", "Read-only access to dashboard and leads", [
        "leads.view", "cms.blog.view", "cms.services.view", "audit.view",
    ]),
]


class Command(BaseCommand):
    help = "Create Feature, roles (Admin + mock roles), and default admin user."

    def handle(self, *args, **options):
        # Create all features
        for name, label in FEATURES_CHOICES:
            Feature.objects.get_or_create(name=name, defaults={"description": label})
        self.stdout.write("Features created.")

        all_features = list(Feature.objects.all())
        feature_by_name = {f.name: f for f in all_features}

        for name, description, perm_names in MOCK_ROLES:
            role, created = UserRole.objects.get_or_create(
                name=name,
                defaults={"description": description or ""},
            )
            if perm_names is None:
                role.features.set(all_features)
            else:
                features = [feature_by_name[p] for p in perm_names if p in feature_by_name]
                role.features.set(features)
            if created:
                self.stdout.write(f"  Role created: {name}")
        self.stdout.write("Roles created (Admin, Sales Manager, Sales Rep, Content Editor, Viewer).")

        # Create default admin user if not exists
        admin_role = UserRole.objects.filter(name="Admin").first()
        if not HubUser.objects.filter(email="admin@alpivot-travels.com").exists():
            HubUser.objects.create_user(
                email="admin@alpivot-travels.com",
                name="Admin User",
                password="admin123",
                role=admin_role,
                avatar="AU",
                is_staff=True,
                is_superuser=True,
            )
            self.stdout.write("Default admin user created: admin@alpivot-travels.com / admin123")
        else:
            self.stdout.write("Admin user already exists.")
