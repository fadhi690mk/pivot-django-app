from rest_framework import serializers
from .models import HubUser, UserRole, Feature


class FeatureSerializer(serializers.ModelSerializer):
    class Meta:
        model = Feature
        fields = ["id", "name", "description"]


class UserRoleSerializer(serializers.ModelSerializer):
    permissions = serializers.SerializerMethodField()
    user_count = serializers.SerializerMethodField()

    class Meta:
        model = UserRole
        fields = ["id", "name", "description", "permissions", "user_count"]

    def get_permissions(self, obj):
        return list(obj.features.values_list("name", flat=True))

    def get_user_count(self, obj):
        return obj.hub_users.count() + obj.users.count()


class HubUserPublicSerializer(serializers.ModelSerializer):
    role = UserRoleSerializer(read_only=True)

    class Meta:
        model = HubUser
        fields = ["id", "name", "email", "avatar", "role"]


class HubUserMeSerializer(serializers.ModelSerializer):
    role = UserRoleSerializer(read_only=True)

    class Meta:
        model = HubUser
        fields = ["id", "name", "email", "avatar", "role"]


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
