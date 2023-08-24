from rest_framework import serializers

from apps.client.models import Contact, Organisation
from apps.pipedrive.models import RoleDetail


class ContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contact
        exclude = ("created_at", "updated_at")


class OrganisationSerializer(serializers.ModelSerializer):
    contacts = serializers.SerializerMethodField()
    created_by = serializers.SerializerMethodField()
    updated_by = serializers.SerializerMethodField()

    class Meta:
        model = Organisation
        exclude = ("created_at", "updated_at")

    def get_created_by(self, instance):
        return instance.created_by.get_full_name()

    def get_updated_by(self, instance):
        return instance.updated_by.get_full_name()

    def get_contacts(self, instance):
        return ContactSerializer(Contact.objects.filter(organisation=instance), many=True).data
