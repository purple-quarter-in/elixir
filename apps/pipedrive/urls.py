from django.urls import path
from rest_framework.routers import DefaultRouter

from apps.pipedrive import views

from .views import LeadViewSet, ProspectViewSet, RoleDetailViewSet

router = DefaultRouter()
router.register("lead", LeadViewSet)
router.register("role_detail", RoleDetailViewSet)
router.register("prospect", ProspectViewSet)
urlpatterns = [path("template", views.say_hello, name="home")]
