from rest_framework.routers import DefaultRouter

from apps.notification.views import NotificationViewSet

router = DefaultRouter()
router.register("notification", NotificationViewSet)
urlpatterns = []
