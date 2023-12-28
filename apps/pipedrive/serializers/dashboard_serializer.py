from rest_framework import serializers

from apps.pipedrive.models import Lead, Prospect


class DashboardRecentLeadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lead
        fields = ["title", "status", "created_at"]


class DashboardRecentProspectSerializer(serializers.ModelSerializer):
    title = serializers.CharField(source="lead.title")

    class Meta:
        model = Prospect
        fields = ["status", "created_at", "title"]


class DashboardLeadSerializer(serializers.Serializer):
    status = serializers.DictField()
    created = serializers.IntegerField()
    owned = serializers.IntegerField()


class DashboardProspectSerializer(serializers.Serializer):
    status = serializers.DictField()
    created = serializers.IntegerField()
    owned = serializers.IntegerField()
