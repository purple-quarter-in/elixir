from django.apps import apps
from rest_framework import serializers

from apps.notification.models import Notification
from apps.pipedrive.models import Activity, Deal, Lead, Prospect
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
        return (
            instance.lead.organisation.get_dict_name_id()
            if instance.lead
            else instance.organisation.get_dict_name_id()
        )

    def get_status(self, instance):
        status = instance.status
        if not instance.closed_at:
            status = None
        return status


class NoteLeadSerializer(serializers.ModelSerializer):
    owner = serializers.SerializerMethodField()
    organisation = serializers.SerializerMethodField()

    class Meta:
        model = Lead
        fields = "__all__"

    def get_organisation(self, instance):
        return instance.organisation.get_dict_name_id()

    def get_owner(self, instance):
        return instance.owner.get_dict_name_id()


class NoteProspectSerializer(serializers.ModelSerializer):
    owner = serializers.SerializerMethodField()
    lead = serializers.SerializerMethodField()

    class Meta:
        model = Prospect
        fields = "__all__"

    def get_lead(self, instance):
        return NoteLeadSerializer(instance.lead).data

    def get_owner(self, instance):
        return instance.owner.get_dict_name_id()


class NoteDealSerializer(serializers.ModelSerializer):
    owner = serializers.SerializerMethodField()
    prospect = serializers.SerializerMethodField()

    class Meta:
        model = Deal
        fields = "__all__"

    def get_prospect(self, instance):
        return NoteProspectSerializer(instance.prospect).data

    def get_owner(self, instance):
        return instance.owner.get_dict_name_id()


class NotificationSerializer(serializers.ModelSerializer):
    data = serializers.SerializerMethodField()

    class Meta:
        model = Notification
        fields = "__all__"

    def get_data(self, instance):
        if instance.object_id:
            model_name = instance.model_name
            if model_name in ["Activity", "Lead", "Prospect", "Deal"]:
                model = apps.get_model("pipedrive", model_name)
                obj = model.objects.get(pk=instance.object_id)
                if model_name == "Lead":
                    return NoteLeadSerializer(obj).data
                elif model_name == "Prospect":
                    return NoteProspectSerializer(obj).data
                elif model_name == "Deal":
                    return NoteDealSerializer(obj).data
                return NoteActivitySerializer(obj).data

        return None
