from django.contrib.auth.models import Group, GroupManager
from django.db import models
from django.utils import timezone

group_manager = GroupManager()
# Create your models here.
Group.add_to_class(
    "created_by",
    models.ForeignKey(
        "user.User",
        on_delete=models.DO_NOTHING,
        default=None,
        null=True,
        related_name="group_created_by_user",
    ),
)
Group.add_to_class(
    "updated_by",
    models.ForeignKey(
        "user.User",
        on_delete=models.DO_NOTHING,
        default=None,
        null=True,
        related_name="group_updated_by_user",
    ),
)
Group.add_to_class("created_at", models.DateTimeField(auto_now_add=True, blank=True, null=True))
Group.add_to_class("updated_at", models.DateTimeField(auto_now=True, blank=True, null=True))

AccessCategoryTypes = (
    ("menu", "Menu"),
    ("administration", "Administration"),
    ("feature", "Feature"),
)


class AccessCategory(models.Model):
    """Model definition for AccessCategory."""

    name = models.CharField(max_length=100)
    code = models.CharField(max_length=100)
    url_frontend = models.CharField(max_length=100, blank=True, null=True)
    type = models.CharField(choices=AccessCategoryTypes, max_length=100)
    parent = models.ForeignKey("self", on_delete=models.DO_NOTHING, null=True, blank=True)
    default_access = models.JSONField(
        default=dict(access=False, view=False, change=True, add=False)
    )
    content_type = models.JSONField(default=list, blank=True, null=True)
    archived = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        """Meta definition for AccessCategory."""

        verbose_name = "AccessCategory"
        verbose_name_plural = "AccessCategorys"

    def save(self, *args, **kwargs):
        """On save, update timestamps"""
        if not self.id:
            self.created_at = timezone.now()
        self.updated_at = timezone.now()
        return super(AccessCategory, self).save(*args, **kwargs)


class GroupCategoryAccessDetail(models.Model):
    """Model definition for GroupCategoryAccessDetail."""

    group = models.ForeignKey(Group, on_delete=models.DO_NOTHING, null=True, blank=True)
    access_category = models.ForeignKey(
        AccessCategory, on_delete=models.DO_NOTHING, null=True, blank=True
    )
    access = models.BooleanField(default=None, null=True)
    view = models.BooleanField(default=None, null=True)
    add = models.BooleanField(default=None, null=True)
    change = models.BooleanField(default=None, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        """Meta definition for GroupCategoryAccessDetail."""

        verbose_name = "GroupCategoryAccessDetail"
        verbose_name_plural = "GroupCategoryAccessDetails"

    def save(self, *args, **kwargs):
        """On save, update timestamps"""
        if not self.id:
            self.created_at = timezone.now()
        self.updated_at = timezone.now()
        return super(GroupCategoryAccessDetail, self).save(*args, **kwargs)


# class CustomGroup(Group):
#     created_by = models.ForeignKey(
#         "user.User",
#         on_delete=models.DO_NOTHING,
#         default=None,
#         null=True,
#         related_name="group_created_by_user",
#     )
#     updated_by = models.ForeignKey(
#         "user.User",
#         on_delete=models.DO_NOTHING,
#         default=None,
#         null=True,
#         related_name="group_updated_by_user",
#     )
#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)
#     objects = group_manager

#     def save(self, *args, **kwargs):
#         """On save, update timestamps"""
#         if not self.id:
#             self.created_at = timezone.now()
#         self.updated_at = timezone.now()
#         return super(CustomGroup, self).save(*args, **kwargs)
