from django.apps import apps
from rest_framework import serializers

from apps.notification.models import Notification
from apps.pipedrive.serializer import ActivitySerializer


class NotificationSerializer(serializers.ModelSerializer):
    data = serializers.SerializerMethodField()

    class Meta:
        model = Notification
        fields = "__all__"

    def get_data(self, instance):
        if instance.object_id:
            model_name = instance.model_name
            if model_name == "Activity":
                model = apps.get_model("pipedrive", model_name)
                obj = model.objects.get(pk=instance.object_id)
                return ActivitySerializer(obj).data

        return None
