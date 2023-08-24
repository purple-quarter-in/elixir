from rest_framework import serializers

from apps.pipedrive.models import Lead, RoleDetail


class CreateLeadSerializer(serializers.Serializer):
    organisation = serializers.DictField()
    role_details = serializers.DictField()
    source = serializers.CharField()


class UpdateLeadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lead
        exclude = ("created_at", "updated_at")


class LeadSerializer(serializers.ModelSerializer):
    created_by = serializers.SerializerMethodField()
    updated_by = serializers.SerializerMethodField()
    owner = serializers.SerializerMethodField()

    class Meta:
        model = Lead
        exclude = ("created_at", "updated_at")

    def get_created_by(self, instance):
        return instance.created_by.get_full_name() if instance.created_by is not None else None

    def get_updated_by(self, instance):
        return instance.updated_by.get_full_name() if instance.updated_by is not None else None

    def get_owner(self, instance):
        return instance.owner.get_full_name() if instance.owner is not None else None


class RoleDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = RoleDetail
        exclude = ("created_at", "updated_at")
