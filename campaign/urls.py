from django.urls import path
from campaign import views
from campaign.views import ContactLeadViewSet
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register("lead", ContactLeadViewSet)
urlpatterns = [
    path("template", views.say_hello, name="home")
]