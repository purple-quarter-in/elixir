from rest_framework import serializers

from apps.client.serializer import OrganisationSerializer
from apps.pipedrive.models import Lead, Prospect, RoleDetail


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
        fields='__all__'

    def get_created_by(self, instance):
        return instance.created_by.get_full_name() if instance.created_by is not None else None

    def get_updated_by(self, instance):
        return instance.updated_by.get_full_name() if instance.updated_by is not None else None

    def get_owner(self, instance):
        return instance.owner.get_full_name() if instance.owner is not None else None

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
        return instance.created_by.get_full_name() if instance.created_by is not None else None

    def get_updated_by(self, instance):
        return instance.updated_by.get_full_name() if instance.updated_by is not None else None

    def get_owner(self, instance):
        return instance.owner.get_full_name() if instance.owner is not None else None

    def get_lead(self, instance):
        return LeadSerializer(instance.lead).data
