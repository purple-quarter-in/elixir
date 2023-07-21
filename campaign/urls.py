from campaign.views import ContactLeadViewSet
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register("lead", ContactLeadViewSet)
