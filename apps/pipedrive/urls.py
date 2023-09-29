from django.urls import path
from rest_framework.routers import DefaultRouter

from apps.pipedrive.views import views
from apps.pipedrive.views.deal_activity_view import ActivityViewSet, NoteViewSet

from .views.views import LeadViewSet, ProspectViewSet, RoleDetailViewSet

router = DefaultRouter()
router.register("lead", LeadViewSet)
router.register("role_detail", RoleDetailViewSet)
router.register("prospect", ProspectViewSet)
router.register("note", NoteViewSet)
router.register("activity", ActivityViewSet)
urlpatterns = [path("template", views.say_hello, name="home")]
