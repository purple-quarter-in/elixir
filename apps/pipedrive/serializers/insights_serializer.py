from rest_framework import serializers

from apps.pipedrive.models import Lead, Prospect


class InsightsRecentLeadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lead
        fields = ["title", "status", "created_at"]


class InsightsRecentProspectSerializer(serializers.ModelSerializer):
    title = serializers.CharField(source="lead.title")

    class Meta:
        model = Prospect
        fields = ["status", "created_at", "title"]


class InsightsLeadSerializer(serializers.Serializer):
    status = serializers.DictField()
    inbound_source = serializers.DictField()
    outbound_source = serializers.DictField()
    lptp = serializers.IntegerField()
    total_leads = serializers.IntegerField()
    created = serializers.IntegerField()
    owned = serializers.IntegerField()


class InsightsLLBSerializer(serializers.Serializer):
    status = serializers.DictField()
    avt = serializers.CharField()
    act = serializers.CharField()
    lpcr = serializers.CharField()
    user_name = serializers.CharField()


class InsightsProspectSerializer(serializers.Serializer):
    status = serializers.DictField()
    pptd = serializers.IntegerField()
    total_prospects = serializers.IntegerField()
    created = serializers.IntegerField()
    owned = serializers.IntegerField()


class InsightsPLBSerializer(serializers.Serializer):
    status = serializers.DictField()
    act = serializers.CharField()
    pdcr = serializers.CharField()
    user_name = serializers.CharField()
