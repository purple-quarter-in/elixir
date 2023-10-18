from django.shortcuts import render
from rest_framework.permissions import IsAuthenticated

from apps.notification.models import Notification
from apps.notification.serialozer import NotificationSerializer
from elixir.utils import custom_success_response
from elixir.viewsets import ModelViewSet


# Create your views here.
class NotificationViewSet(ModelViewSet):
    queryset = Notification.objects.all().filter(archived=False).order_by("-created_at")
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]

    def list(self, request, *args, **kwargs):
        queryset = self.queryset.filter(user=request.user)
        return custom_success_response(self.serializer_class(queryset, many=True).data)


def schedule_create_notification(instance, type, description, user, model_name):
    Notification.objects.create(
        type=type,
        description=description,
        user=user,
        model_name=model_name,
        object_id=instance.id if instance else None,
    )
