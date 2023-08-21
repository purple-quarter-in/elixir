from django.urls import path
from .views import *
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register("rbac/category-access", AccessCategoryViewset)
router.register("rbac/profile", GroupCategoryAccessDetailViewset)
urlpatterns = []
