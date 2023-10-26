from django import db
from django.shortcuts import render
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated

from apps.notification.models import Notification
from apps.notification.serialozer import NotificationSerializer
from elixir.utils import custom_success_response
from elixir.viewsets import ModelViewSet


# Create your views here.
class NotificationViewSet(ModelViewSet):
    queryset = Notification.objects.all().filter(archived=False).order_by("-created_at")
    serializer_class = NotificationSerializer

    def list(self, request, *args, **kwargs):
        queryset = self.queryset.filter(user=request.user)
        return custom_success_response(self.serializer_class(queryset, many=True).data)

    @action(detail=False, methods=["post"])
    def schedule_create_notification(self, request):
        serializer = NotificationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return custom_success_response({"message": "Notification created"})

    @action(detail=False, methods=["delete"])
    def bulk_delete(self, request):
        Notification.objects.filter(user=request.user).delete()
        return custom_success_response({"message": "All Notifications has been deleted"})
