from rest_framework import serializers

from apps.pipedrive.models import Lead, Prospect


class DashboardRecentLeadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lead
        fields = ["title", "status", "created_at"]


class DashboardRecentProspectSerializer(serializers.ModelSerializer):
    title = serializers.CharField(source="lead.title")
    service_fee_range = serializers.CharField(source="lead.service_fee_range")
    fixed_budget = serializers.CharField(source="lead.role.fixed_budget")

    class Meta:
        model = Prospect
        fields = ["title", "service_fee_range", "fixed_budget"]
