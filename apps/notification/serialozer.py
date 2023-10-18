from django.apps import apps
from rest_framework import serializers

from apps.notification.models import Notification
from apps.pipedrive.models import Activity
from apps.pipedrive.serializer import NotesContactSerializer


class NoteActivitySerializer(serializers.ModelSerializer):
    contacts = serializers.SerializerMethodField()
    created_by = serializers.SerializerMethodField()
    assigned_to = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()
    organisation = serializers.SerializerMethodField()

    class Meta:
        model = Activity
        fields = "__all__"
        extra_kwargs = {"created_by": {"read_only": True}}

    def get_created_by(self, instance):
        return instance.created_by.get_dict_name_id() if instance.created_by is not None else None

    def get_assigned_to(self, instance):
        return (
            instance.assigned_to.get_dict_name_id() if instance.assigned_to is not None else None
        )

    def get_contacts(self, instance):
        return NotesContactSerializer(instance.contact, many=True).data

    def get_organisation(self, instance):
        return instance.lead.organisation.get_dict_name_id()

    def get_status(self, instance):
        status = instance.status
        if not instance.closed_at:
            status = None
        return status


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
                return NoteActivitySerializer(obj).data

        return None
