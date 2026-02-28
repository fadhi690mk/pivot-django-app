from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenRefreshView
from rest_framework_simplejwt.exceptions import InvalidToken

from accounts.permissions import HasHubPermission
from .models import HubUser, UserRole
from .serializers import HubUserMeSerializer, LoginSerializer, UserRoleSerializer


# Menu items for hub sidebar: (path_prefix, label, permission required to see)
# Section order and labels are kept on frontend; this defines permission per item.
HUB_MENU_ITEMS = [
    ("/hub", "Dashboard", "leads.view"),
    ("/hub/leads", "All Leads", "leads.view"),
    ("/hub/pipeline", "Pipeline", "leads.view"),
    ("/hub/invoices", "Invoices & Receipts", "invoices.view"),
    ("/hub/cms/hero", "Hero Slides", "cms.hero.edit"),
    ("/hub/cms/services", "Services", "cms.services.view"),
    ("/hub/cms/blog", "Blog Posts", "cms.blog.view"),
    ("/hub/cms/news", "News", "cms.news.edit"),
    ("/hub/cms/team", "Team", "cms.team.edit"),
    ("/hub/cms/clients", "Clients", "cms.clients.edit"),
    ("/hub/cms/agencies", "Government Agencies", "cms.pages.edit"),
    ("/hub/cms/testimonials", "Testimonials", "cms.testimonials.edit"),
    ("/hub/cms/faqs", "FAQs", "cms.faq.edit"),
    ("/hub/config/calculator", "Calculator", "config.calculator"),
    ("/hub/config/search", "Search Suggestions", "config.search"),
    ("/hub/config/roles", "Roles & Permissions", "config.roles"),
    ("/hub/audit-log", "Audit Log", "audit.view"),
    ("/hub/settings", "Settings", "settings.manage"),
]


def get_allowed_menu(user):
    """Return list of menu items the user is allowed to see: [{ to, label }, ...]."""
    perms = user.get_permission_names()
    return [
        {"to": to, "label": label}
        for to, label, perm in HUB_MENU_ITEMS
        if perm in perms
    ]


def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)
    return {"access": str(refresh.access_token), "refresh": str(refresh)}


@api_view(["POST"])
@permission_classes([AllowAny])
def login(request):
    serializer = LoginSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    email = serializer.validated_data["email"]
    password = serializer.validated_data["password"]
    user = HubUser.objects.filter(email=email, is_deleted=False).first()
    if not user or not user.check_password(password):
        return Response({"detail": "Invalid credentials."}, status=status.HTTP_401_UNAUTHORIZED)
    if not user.is_active:
        return Response({"detail": "User is inactive."}, status=status.HTTP_401_UNAUTHORIZED)
    tokens = get_tokens_for_user(user)
    from .serializers import HubUserPublicSerializer
    from audit.utils import log_audit
    log_audit(request, "login", "auth", "Hub login", target_id=str(user.id), details=user.email)
    return Response({
        "access": tokens["access"],
        "refresh": tokens["refresh"],
        "user": HubUserPublicSerializer(user).data,
        "permissions": list(user.get_permission_names()),
        "menu": get_allowed_menu(user),
    })


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def me(request):
    user = request.user
    data = HubUserMeSerializer(user).data
    data["permissions"] = list(user.get_permission_names())
    data["menu"] = get_allowed_menu(user)
    return Response(data)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def menu(request):
    """Return menu items the current user is allowed to see (for hub sidebar)."""
    return Response({"menu": get_allowed_menu(request.user), "permissions": list(request.user.get_permission_names())})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def logout(request):
    refresh = request.data.get("refresh")
    if not refresh:
        return Response({"detail": "refresh token required"}, status=status.HTTP_400_BAD_REQUEST)
    try:
        token = RefreshToken(refresh)
        token.blacklist()
    except Exception:
        pass
    return Response(status=status.HTTP_205_RESET_CONTENT)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def register_fcm(request):
    """Register FCM token for push notifications (e.g. new leads). Subscribes token to topic hub_leads."""
    import logging
    logger = logging.getLogger(__name__)
    token = request.data.get("token") if isinstance(request.data, dict) else None
    if not token or not isinstance(token, str):
        logger.warning("register_fcm: missing or invalid token")
        return Response({"detail": "token is required."}, status=status.HTTP_400_BAD_REQUEST)
    from awamer.firebase_fcm import subscribe_token_to_topic
    if subscribe_token_to_topic(token):
        logger.info("FCM: Token subscribed to hub_leads (register-fcm 204)")
        return Response(status=status.HTTP_204_NO_CONTENT)
    logger.warning("FCM: Failed to subscribe token (register-fcm 503)")
    return Response({"detail": "Failed to subscribe token."}, status=status.HTTP_503_SERVICE_UNAVAILABLE)


@api_view(["GET"])
@permission_classes([IsAuthenticated, HasHubPermission])
def user_list(request):
    """List hub users (id, name) for lead assign dropdown etc."""
    user_list.required_permission = "leads.assign"
    qs = HubUser.objects.filter(is_active=True, is_deleted=False).order_by("name")
    return Response([{"id": str(u.id), "name": u.name} for u in qs])


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated, HasHubPermission])
def role_list(request):
    if request.method == "POST":
        from .models import Feature
        from audit.utils import log_audit
        name = (request.data.get("name") or "").strip()
        if not name:
            return Response({"detail": "name is required"}, status=status.HTTP_400_BAD_REQUEST)
        if UserRole.objects.filter(name=name, is_deleted=False).exists():
            return Response({"detail": "A role with this name already exists."}, status=status.HTTP_400_BAD_REQUEST)
        description = (request.data.get("description") or "")[:500]
        perm_names = request.data.get("permissions")
        if not isinstance(perm_names, list):
            perm_names = []
        features = list(Feature.objects.filter(name__in=perm_names).values_list("id", flat=True))
        role = UserRole.objects.create(name=name, description=description)
        role.features.set(features)
        role.refresh_from_db()
        role = UserRole.objects.prefetch_related("features").get(pk=role.pk)
        log_audit(request, "create", "config", f"Role {role.name}", str(role.id), "Role created")
        return Response(UserRoleSerializer(role).data, status=status.HTTP_201_CREATED)
    qs = UserRole.objects.prefetch_related("features").filter(is_deleted=False).order_by("name")
    return Response(UserRoleSerializer(qs, many=True).data)


role_list.required_permissions = {"GET": "config.roles", "POST": "config.roles"}


@api_view(["GET", "PATCH", "DELETE"])
@permission_classes([IsAuthenticated, HasHubPermission])
def role_detail(request, pk):
    try:
        role = UserRole.objects.prefetch_related("features").get(pk=pk, is_deleted=False)
    except UserRole.DoesNotExist:
        return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
    if request.method == "DELETE":
        from audit.utils import log_audit
        if role.name == "Admin":
            return Response({"detail": "Cannot delete Admin role."}, status=status.HTTP_400_BAD_REQUEST)
        name = role.name
        role.is_deleted = True
        role.save(update_fields=["is_deleted"])
        log_audit(request, "delete", "config", f"Role {name}", str(pk), "Role soft-deleted")
        return Response(status=status.HTTP_204_NO_CONTENT)
    if request.method == "PATCH":
        from .models import Feature
        from audit.utils import log_audit
        data = request.data
        if data.get("name") is not None:
            name = (data.get("name") or "").strip()
            if name and name != role.name:
                if UserRole.objects.filter(name=name, is_deleted=False).exclude(pk=role.pk).exists():
                    return Response({"detail": "A role with this name already exists."}, status=status.HTTP_400_BAD_REQUEST)
                role.name = name
        if data.get("description") is not None:
            role.description = (data.get("description") or "")[:500]
        if "permissions" in data:
            perm_names = data["permissions"] if isinstance(data["permissions"], list) else []
            features = list(Feature.objects.filter(name__in=perm_names).values_list("id", flat=True))
            role.features.set(features)
        role.save()
        role.refresh_from_db()
        role = UserRole.objects.prefetch_related("features").get(pk=role.pk)
        log_audit(request, "update", "config", f"Role {role.name}", str(role.id), "Role updated")
        return Response(UserRoleSerializer(role).data)
    return Response(UserRoleSerializer(role).data)


role_detail.required_permissions = {"GET": "config.roles", "PATCH": "config.roles", "DELETE": "config.roles"}


@api_view(["POST"])
@permission_classes([IsAuthenticated, HasHubPermission])
def send_reset_link(request):
    """Send password reset link to a hub user by email. Requires cms.team.edit."""
    send_reset_link.required_permissions = {"POST": "cms.team.edit"}
    email = (request.data.get("email") or "").strip()
    if not email:
        return Response({"detail": "email is required."}, status=status.HTTP_400_BAD_REQUEST)
    user = HubUser.objects.filter(email__iexact=email, is_deleted=False).first()
    if not user:
        return Response({"detail": "No hub user found with this email."}, status=status.HTTP_404_NOT_FOUND)
    from django.contrib.auth.tokens import default_token_generator
    from django.core.mail import send_mail
    from django.conf import settings
    from django.utils.http import urlsafe_base64_encode
    from django.utils.encoding import force_bytes

    token = default_token_generator.make_token(user)
    uid = urlsafe_base64_encode(force_bytes(str(user.pk)))
    frontend_url = getattr(settings, "FRONTEND_URL", None) or request.build_absolute_uri("/").rstrip("/")
    reset_url = f"{frontend_url}/set-password?uid={uid}&token={token}"
    subject = "Reset your Hub password"
    message = f"Hello {user.name},\n\nYou requested a password reset for the Management Hub.\n\nSet a new password here: {reset_url}\n\nIf you did not request this, ignore this email.\n\n— Al Awamer"
    try:
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=False,
        )
    except Exception as e:
        return Response({"detail": f"Failed to send email: {str(e)}"}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
    return Response({"detail": "Reset link sent."}, status=status.HTTP_200_OK)


@api_view(["POST"])
@permission_classes([IsAuthenticated, HasHubPermission])
def send_invite(request):
    """Send invite (set-password link) to a hub user by user_id. Requires cms.team.edit."""
    send_invite.required_permissions = {"POST": "cms.team.edit"}
    user_id = request.data.get("user_id")
    if not user_id:
        return Response({"detail": "user_id is required."}, status=status.HTTP_400_BAD_REQUEST)
    try:
        user = HubUser.objects.get(pk=user_id, is_deleted=False)
    except (HubUser.DoesNotExist, ValueError):
        return Response({"detail": "User not found."}, status=status.HTTP_404_NOT_FOUND)
    from django.contrib.auth.tokens import default_token_generator
    from django.core.mail import send_mail
    from django.conf import settings
    from django.utils.http import urlsafe_base64_encode
    from django.utils.encoding import force_bytes

    token = default_token_generator.make_token(user)
    uid = urlsafe_base64_encode(force_bytes(str(user.pk)))
    frontend_url = getattr(settings, "FRONTEND_URL", None) or request.build_absolute_uri("/").rstrip("/")
    invite_url = f"{frontend_url}/set-password?uid={uid}&token={token}"
    subject = "You're invited to the Management Hub"
    message = f"Hello {user.name},\n\nYou have been invited to the Management Hub.\n\nSet your password here: {invite_url}\n\n— Al Awamer"
    try:
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=False,
        )
    except Exception as e:
        return Response({"detail": f"Failed to send email: {str(e)}"}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
    return Response({"detail": "Invite sent."}, status=status.HTTP_200_OK)


@api_view(["POST"])
@permission_classes([AllowAny])
def confirm_reset(request):
    """Set new password from reset/invite link. Body: uid (base64), token, new_password."""
    uid = request.data.get("uid")
    token = request.data.get("token")
    new_password = (request.data.get("new_password") or "").strip()
    if not uid or not token:
        return Response({"detail": "uid and token are required."}, status=status.HTTP_400_BAD_REQUEST)
    if not new_password or len(new_password) < 8:
        return Response({"detail": "new_password must be at least 8 characters."}, status=status.HTTP_400_BAD_REQUEST)
    from django.contrib.auth.tokens import default_token_generator
    from django.utils.http import urlsafe_base64_decode
    from django.utils.encoding import force_str

    try:
        pk = force_str(urlsafe_base64_decode(uid))
        user = HubUser.objects.get(pk=pk, is_deleted=False)
    except (TypeError, ValueError, OverflowError, HubUser.DoesNotExist):
        return Response({"detail": "Invalid or expired link."}, status=status.HTTP_400_BAD_REQUEST)
    if not default_token_generator.check_token(user, token):
        return Response({"detail": "Invalid or expired link."}, status=status.HTTP_400_BAD_REQUEST)
    user.set_password(new_password)
    user.save(update_fields=["password"])
    return Response({"detail": "Password set. You can now log in."}, status=status.HTTP_200_OK)
