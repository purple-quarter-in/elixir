from django.urls import path
from pipedrive import views
from pipedrive.views import ContactLeadViewSet
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register("lead", ContactLeadViewSet)
urlpatterns = [
    path("template", views.say_hello, name="home")
]