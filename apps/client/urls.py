from rest_framework.routers import DefaultRouter

from .views import ContactViewSet, OrganisationViewSet

router = DefaultRouter()
router.register("client/contact", ContactViewSet)
router.register("client", OrganisationViewSet)
urlpatterns = []
