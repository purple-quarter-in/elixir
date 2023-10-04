from django.db import connection
from rest_framework import serializers

from apps.client.models import Contact
from apps.client.serializer import OrganisationSerializer
from apps.pipedrive.models import Activity, Lead, Note, Prospect, RoleDetail, changelog


class CreateLeadSerializer(serializers.Serializer):
    organisation = serializers.DictField()
    role_details = serializers.DictField()
    source = serializers.CharField()


class UpdateLeadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lead
        exclude = ("created_at", "updated_at")


class UpdateProspectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Prospect
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
        exclude = ["updated_at"]
        depth = 1

    def get_created_by(self, instance):
        return instance.created_by.get_dict_name_id() if instance.created_by is not None else None

    def get_updated_by(self, instance):
        return instance.updated_by.get_dict_name_id() if instance.updated_by is not None else None

    def get_owner(self, instance):
        return instance.owner.get_dict_name_id() if instance.owner is not None else None

    def get_lead(self, instance):
        return LeadSerializer(instance.lead).data


class DropDownActivitySerializer(serializers.ModelSerializer):
    contacts = serializers.SerializerMethodField()

    class Meta:
        model = Activity
        fields = ["id", "mode", "type", "title", "contacts"]

    def get_contacts(self, instance):
        cursor = connection.cursor()
        cursor.execute(
            f"select contact_id from pipedrive_activity_contact where activity_id = {instance.id}"
        )
        list_of_ids = [row[0] for row in cursor.fetchall()]
        return NotesContactSerializer(Contact.objects.filter(id__in=list_of_ids), many=True).data


class ActivitySerializer(serializers.ModelSerializer):
    contacts = serializers.SerializerMethodField()
    created_by = serializers.SerializerMethodField()
    assigned_to = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()

    class Meta:
        model = Activity
        fields = "__all__"
        extra_kwargs = {"created_by": {"read_only": True}}

    def create(self, validated_data):
        validated_data["created_by"] = self.context["request"].user
        validated_data["assigned_to_id"] = self.context["request"].data.get("assigned_to", None)
        count = Activity.objects.filter(
            lead=validated_data["lead"], type=validated_data["type"]
        ).count()
        validated_data["title"] = validated_data["type"] + " - " + f"{count+1}".zfill(2)
        return super().create(validated_data)

    def get_created_by(self, instance):
        return instance.created_by.get_dict_name_id() if instance.created_by is not None else None

    def get_assigned_to(self, instance):
        return (
            instance.assigned_to.get_dict_name_id() if instance.assigned_to is not None else None
        )

    def get_contacts(self, instance):
        return NotesContactSerializer(instance.contact, many=True).data

    def get_status(self, instance):
        status = instance.status
        if not instance.closed_at:
            status = None
        return status


class NotesContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contact
        fields = ["name", "email", "std_code", "phone", "designation"]


class NoteSerializer(serializers.ModelSerializer):
    activity = serializers.SerializerMethodField()
    created_by = serializers.SerializerMethodField()

    class Meta:
        model = Note
        fields = "__all__"
        extra_kwargs = {"created_by": {"read_only": True}}

    def create(self, validated_data):
        validated_data["created_by"] = self.context["request"].user
        validated_data["activity_id"] = self.context["request"].data.get("activity", None)
        return super().create(validated_data)

    def get_created_by(self, instance):
        return instance.created_by.get_dict_name_id() if instance.created_by is not None else None

    def get_activity(self, instance):
        return (
            ActivitySerializer(instance.activity).data if instance.activity is not None else None
        )


class HistoryNoteSerializer(serializers.ModelSerializer):
    activity_type = serializers.CharField(source="activity.type")
    mode = serializers.CharField(source="activity.mode")
    title = serializers.CharField(source="activity.title")
    contacts = serializers.SerializerMethodField()
    created_by = serializers.SerializerMethodField()

    class Meta:
        model = Note
        fields = "__all__"
        extra_kwargs = {"created_by": {"read_only": True}}

    def get_contacts(self, instance):
        return NotesContactSerializer(instance.activity.contact, many=True).data

    def get_created_by(self, instance):
        return instance.created_by.get_dict_name_id() if instance.created_by is not None else None


class ChangelogSerializer(serializers.ModelSerializer):
    changed_by = serializers.SerializerMethodField()

    class Meta:
        model = changelog
        exclude = ["model_name", "obj_id"]

    def get_changed_by(self, instance):
        return instance.changed_by.get_dict_name_id() if instance.changed_by is not None else None
