from django.urls import re_path
from rest_framework.routers import DefaultRouter

from .views import *

router = DefaultRouter()
router.register("users", UserViewSet)

urlpatterns = [
    re_path("login/$", Login.as_view(), name="user_login"),
]
