from campaign.models import ContactLead
from rest_framework import serializers


class ContactLeadSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContactLead
        exclude = ("created_at", "updated_at")
