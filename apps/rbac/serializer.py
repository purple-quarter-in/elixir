from rest_framework import serializers

from .models import *


class AccessCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = AccessCategory
        exclude = ("created_at", "updated_at", "archived")


class GroupCategoryAccessDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = GroupCategoryAccessDetail
        exclude = ("created_at", "updated_at", "archived")


class GETGroupCategoryAccessDetailSerializer(serializers.Serializer):
    group_details = serializers.DictField()
    permissions = serializers.ListField()
