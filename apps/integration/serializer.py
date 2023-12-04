from rest_framework import serializers

from apps.integration.models import Integration


class IntegrationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Integration
        fields = ["id", "service_name", "archived", "user_email", "created_at", "auth_type"]
