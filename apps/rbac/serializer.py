from rest_framework import serializers

from apps.user.models import User
from apps.user.serializer import GetUserSerializer

from .models import *


class AccessCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = AccessCategory
        exclude = ("created_at", "updated_at", "archived")


class GroupCategoryAccessDetailSerializer(serializers.ModelSerializer):
    access_category = serializers.SerializerMethodField()

    class Meta:
        model = GroupCategoryAccessDetail
        exclude = ("created_at", "updated_at")

    def get_access_category(self, instance):
        return AccessCategorySerializer(instance.access_category).data


class GETGroupCategoryAccessDetailSerializer(serializers.Serializer):
    group_details = serializers.DictField()
    permissions = serializers.ListField()


class GroupSerializer(serializers.ModelSerializer):
    permissions = serializers.SerializerMethodField()

    class Meta:
        model = Group
        fields = "__all__"
        depth = 1


class GroupSerializer(serializers.ModelSerializer):
    permissions = serializers.SerializerMethodField()
    created_by = serializers.SerializerMethodField()
    updated_by = serializers.SerializerMethodField()
    users = serializers.SerializerMethodField()
    # access_category = serializers.SerializerMethodField()

    class Meta:
        model = Group
        fields = [
            "id",
            "name",
            "created_by",
            "updated_by",
            "permissions",
            "created_at",
            "updated_at",
            "users",
        ]

    def get_permissions(self, instance):
        return GroupCategoryAccessDetailSerializer(
            GroupCategoryAccessDetail.objects.filter(group_id=instance.id), many=True
        ).data

    def get_created_by(self, instance):
        return instance.created_by.get_full_name()

    def get_updated_by(self, instance):
        return instance.updated_by.get_full_name()

    def get_users(self, instance):
        return GetUserSerializer(User.objects.filter(groups__id=instance.id), many=True).data
