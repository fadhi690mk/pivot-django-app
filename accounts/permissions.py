from rest_framework.permissions import BasePermission


class HasHubPermission(BasePermission):
    def has_permission(self, request, view):
        required = getattr(view, "required_permission", None)
        if required is None:
            perms = getattr(view, "required_permissions", None)
            if perms:
                required = perms.get(request.method)
        if not required:
            return True
        user = request.user
        if not user.is_authenticated:
            return False
        if getattr(user, "role", None) and not getattr(user.role, "is_deleted", True):
            if user.role.features.filter(name=required).exists():
                return True
        return user.roles.filter(features__name=required).exists()
