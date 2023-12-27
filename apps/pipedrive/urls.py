from django.urls import path
from rest_framework.routers import DefaultRouter

from apps.pipedrive.aggregations.lead import (
    lead_aggregate_monthly,
    lead_aggregate_quarterly,
    lead_aggregate_weekly,
    lead_aggregate_yearly,
)
from apps.pipedrive.aggregations.prospect import (
    prospect_aggregate_monthly,
    prospect_aggregate_quarterly,
    prospect_aggregate_weekly,
    prospect_aggregate_yearly,
)
from apps.pipedrive.views import views
from apps.pipedrive.views.dashboard_view import (
    DashboardLeadViewSet,
    DashboardProspectViewSet,
)
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
## dashboard
router.register("dashboard/lead", DashboardLeadViewSet)
router.register("dashboard/prospect", DashboardProspectViewSet)
urlpatterns = [
    path("import-organisation", views.org_import),
    path("import-contact", views.contact_import),
    path("history/activity/", view=History.as_view()),
    path("landingpage/createlead/", CreateLandingPageLead.as_view()),
    path("schedular/aggregation/lead/weekly/", lead_aggregate_weekly),
    path("schedular/aggregation/lead/monthly/", lead_aggregate_monthly),
    path("schedular/aggregation/lead/quarterly/", lead_aggregate_quarterly),
    path("schedular/aggregation/lead/yearly/", lead_aggregate_yearly),
    path("schedular/aggregation/prospect/weekly/", prospect_aggregate_weekly),
    path("schedular/aggregation/prospect/monthly/", prospect_aggregate_monthly),
    path("schedular/aggregation/prospect/quarterly/", prospect_aggregate_quarterly),
    path("schedular/aggregation/prospect/yearly/", prospect_aggregate_yearly),
]
