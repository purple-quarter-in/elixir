from django.contrib import admin
from django.contrib.auth.models import Permission

from apps.rbac.models import AccessCategory, GroupCategoryAccessDetail

# Register your models here.
admin.site.register(GroupCategoryAccessDetail)
admin.site.register(AccessCategory)
admin.site.register(Permission)
