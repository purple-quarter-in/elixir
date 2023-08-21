import json
from datetime import datetime
from email.policy import default
from os import name
from random import random
from urllib import response

import pytz
from django.contrib.auth.models import Group, Permission
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated

from apps.rbac.models import AccessCategory, GroupCategoryAccessDetail
from apps.rbac.serializer import (
    AccessCategorySerializer,
    GETGroupCategoryAccessDetailSerializer,
    GroupCategoryAccessDetailSerializer,
)
from elixir.utils import custom_success_response
from elixir.viewsets import ModelViewSet


# Create your views here.
class AccessCategoryViewset(ModelViewSet):
    # permission_classes = [IsAuthenticated]
    queryset = AccessCategory.objects.all()
    serializer_class = AccessCategorySerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return custom_success_response(serializer.data, status=status.HTTP_201_CREATED)

    # @action(detail=False, methods=["get"])
    # def cycle_start_date_list(self, request):
    #     return custom_success_response(
    #         {
    #             "input_items": [
    #                 {"item_code": x[0], "item_name": x[1]}
    #                 for x in CYCLE_START_DATE_CHOICE
    #             ]
    #         }
    #     )


class GroupCategoryAccessDetailViewset(ModelViewSet):
    permission_classes = [IsAuthenticated]
    queryset = GroupCategoryAccessDetail.objects.all()
    serializer_class = GroupCategoryAccessDetailSerializer

    def list(self, request):
        if not request.user.has_perm("pipedrive.access_lead"):
            raise PermissionDenied()
        return custom_success_response(
            {"permission": request.user.has_perm("pipedrive.access_lead")}
        )

    def create(self, request, *args, **kwargs):
        GETserializer = GETGroupCategoryAccessDetailSerializer(data=request.data)
        GETserializer.is_valid(raise_exception=True)
        if Group.objects.filter(
            name=GETserializer.validated_data["group_details"]["name"]
        ).exists():
            raise ValidationError(
                {"group name": ["Group with provide name already exists"]}
            )
        group = Group.objects.create(
            name=GETserializer.validated_data["group_details"]["name"]
        )
        permission_ids = []
        for permission in GETserializer.validated_data["permissions"]:
            access_category = AccessCategory.objects.get(
                id=permission["access_category"]
            )
            permission.pop("access_category")
            gcad = GroupCategoryAccessDetail.objects.create(
                **permission, group=group, access_category=access_category
            )
            content_type_list = access_category.content_type
            for content_type in content_type_list:
                auth_permission_list = Permission.objects.filter(
                    content_type_id=content_type
                )
                auth_permission_dict = {
                    (x.codename).split("_")[0]: x for x in auth_permission_list
                }
                for x, value in permission.items():
                    if value == 1:
                        permission_ids.append(auth_permission_dict[x].id)
        for id in permission_ids:
            group.permissions.add(id)
        return custom_success_response(
            {"Group created successfully"}, status=status.HTTP_201_CREATED
        )

    def update(self, request, *args, **kwargs):
        GETserializer = GETGroupCategoryAccessDetailSerializer(data=request.data)
        GETserializer.is_valid(raise_exception=True)
        group_details = request.data.get("group_details")
        group = Group.objects.get(id=group_details["id"])
        if "name" in group_details and group.name != group_details["name"]:
            group.name = request.data.get("name", group.name)
            group.save()
        group.permissions.clear()
        permission_ids = []
        for permission in GETserializer.validated_data["permissions"]:
            access_category = AccessCategory.objects.get(
                id=permission["access_category"]
            )
            permission.pop("access_category")
            gcad = GroupCategoryAccessDetail.objects.update_or_create(
                group=group,
                access_category=access_category,
                defaults={**permission},
            )
            content_type_list = access_category.content_type
            for content_type in content_type_list:
                auth_permission_list = Permission.objects.filter(
                    content_type_id=content_type
                )
                auth_permission_dict = {
                    (x.codename).split("_")[0]: x for x in auth_permission_list
                }
                for x, value in permission.items():
                    if value == 1:
                        permission_ids.append(auth_permission_dict[x].id)
        for id in permission_ids:
            group.permissions.add(id)
        return custom_success_response(
            {"Group permission updated successfully"}, status=status.HTTP_201_CREATED
        )
