from django.urls import path
from rest_framework.routers import DefaultRouter

from apps.pipedrive.views import views
from apps.pipedrive.views.deal_activity_view import (
    ActivityViewSet,
    History,
    NoteViewSet,
)

from .views.views import (
    CreateLandingPageLead,
    DealViewSet,
    LeadViewSet,
    ProspectViewSet,
    RDCapsuleViewSet,
    RoleDetailViewSet,
    ServiceContractViewSet,
    ServiceProposalViewSet,
)

router = DefaultRouter()
router.register("lead", LeadViewSet)
router.register("role_detail", RoleDetailViewSet)
router.register("prospect", ProspectViewSet)
router.register("deal", DealViewSet)
router.register("note", NoteViewSet)
router.register("activity", ActivityViewSet)
router.register("contract", ServiceContractViewSet)
router.register("rdcapsule", RDCapsuleViewSet)
router.register("proposal", ServiceProposalViewSet)
urlpatterns = [
    path("import-organisation", views.org_import),
    path("import-contact", views.contact_import),
    path("history/activity/", view=History.as_view()),
    path("landingpage/createlead/", CreateLandingPageLead.as_view()),
]
