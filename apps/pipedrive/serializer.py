from rest_framework import serializers

from apps.client.models import Contact
from apps.client.serializer import OrganisationSerializer
from apps.pipedrive.models import Activity, Lead, Note, Prospect, RoleDetail


class CreateLeadSerializer(serializers.Serializer):
    organisation = serializers.DictField()
    role_details = serializers.DictField()
    source = serializers.CharField()


class UpdateLeadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lead
        exclude = ("created_at", "updated_at")


class RoleDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = RoleDetail
        exclude = ("created_at", "updated_at")


class LeadSerializer(serializers.ModelSerializer):
    created_by = serializers.SerializerMethodField()
    updated_by = serializers.SerializerMethodField()
    owner = serializers.SerializerMethodField()
    role = serializers.SerializerMethodField()
    organisation = serializers.SerializerMethodField()

    class Meta:
        model = Lead
        fields = "__all__"

    def get_created_by(self, instance):
        return instance.created_by.get_dict_name_id() if instance.created_by is not None else None

    def get_updated_by(self, instance):
        return instance.updated_by.get_dict_name_id() if instance.updated_by is not None else None

    def get_owner(self, instance):
        return instance.owner.get_dict_name_id() if instance.owner is not None else None

    def get_role(self, instance):
        return RoleDetailSerializer(instance.role).data

    def get_organisation(self, instance):
        return OrganisationSerializer(instance.organisation).data


class ProspectSerializer(serializers.ModelSerializer):
    created_by = serializers.SerializerMethodField()
    updated_by = serializers.SerializerMethodField()
    owner = serializers.SerializerMethodField()
    lead = serializers.SerializerMethodField()

    class Meta:
        model = Prospect
        exclude = ("created_at", "updated_at")
        depth = 1

    def get_created_by(self, instance):
        return instance.created_by.get_dict_name_id() if instance.created_by is not None else None

    def get_updated_by(self, instance):
        return instance.updated_by.get_dict_name_id() if instance.updated_by is not None else None

    def get_owner(self, instance):
        return instance.owner.get_dict_name_id() if instance.owner is not None else None

    def get_lead(self, instance):
        return LeadSerializer(instance.lead).data


class ActivitySerializer(serializers.ModelSerializer):
    contacts = serializers.SerializerMethodField()
    created_by = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()

    class Meta:
        model = Activity
        fields = "__all__"
        extra_kwargs = {"created_by": {"read_only": True}}

    def create(self, validated_data):
        validated_data["created_by"] = self.context["request"].user
        return super().create(validated_data)

    def get_created_by(self, instance):
        return instance.created_by.get_dict_name_id() if instance.created_by is not None else None

    def get_contacts(self, instance):
        return NotesContactSerializer(instance.contact, many=True).data

    def get_status(self, instance):
        status = instance.status
        if not instance.closed_at:
            status = ""
        return status


class NotesContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contact
        fields = ["name", "email", "std_code", "phone", "designation"]


class NoteSerializer(serializers.ModelSerializer):
    contacts = serializers.SerializerMethodField()
    created_by = serializers.SerializerMethodField()

    class Meta:
        model = Note
        fields = "__all__"
        extra_kwargs = {"created_by": {"read_only": True}}

    def create(self, validated_data):
        validated_data["created_by"] = self.context["request"].user
        return super().create(validated_data)

    def get_created_by(self, instance):
        return instance.created_by.get_dict_name_id() if instance.created_by is not None else None

    def get_contacts(self, instance):
        return NotesContactSerializer(instance.contact, many=True).data
