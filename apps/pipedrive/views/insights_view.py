from datetime import date, datetime, timedelta

from django.db.models import Q
from django.shortcuts import render
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated

from apps.pipedrive.aggregations.helper import (
    calc_lead_verificarion_closure_conversion_rate,
    calc_prospect_closure_conversion_rate,
    get_recent_leads,
    recent_prospects,
    required_check,
)
from apps.pipedrive.aggregations.lead import lead_aggregate
from apps.pipedrive.aggregations.prospect import prospect_aggregate
from apps.pipedrive.models import Lead, Prospect
from apps.pipedrive.serializer import LeadSerializer, ProspectSerializer
from apps.pipedrive.serializers.insights_serializer import (
    InsightsLeadSerializer,
    InsightsLLBSerializer,
    InsightsPLBSerializer,
    InsightsProspectSerializer,
    InsightsRecentLeadSerializer,
    InsightsRecentProspectSerializer,
)
from apps.user.models import User
from elixir.mongo_client import get_db_handle_conn_string
from elixir.utils import (
    custom_success_response,
    get_current_fiscal_year_range,
    get_current_quarter_range,
    get_start_end_month,
    get_start_end_week,
)
from elixir.viewsets import ModelViewSet


# Create your views here.
class InsightLeadViewSet(ModelViewSet):
    queryset = Lead.objects.all()
    serializer_class = LeadSerializer
    permission_classes = [IsAuthenticated]

    # http_method_names = ["get", "post"]

    @action(methods=["get"], detail=False)
    def summary_with_recent_leads(self, request):
        user = int(request.query_params.get("user", None))
        rl = InsightsRecentLeadSerializer(get_recent_leads(user), many=True).data
        fiscal_start, fiscal_end = get_current_fiscal_year_range(datetime.now())
        Leads = Lead.objects.filter(
            created_at__gte=fiscal_start,
            created_at__lte=fiscal_end,
        ).values(
            "created_at", "verification_time", "closure_time", "is_converted_to_prospect", "ageing"
        )
        if user:
            Leads = Leads.filter(Q(created_by_id=user) | Q(owner_id=user))
        data = calc_lead_verificarion_closure_conversion_rate(Leads)
        return custom_success_response({"recent_leads": rl, **data})

    @action(methods=["get"], detail=False)
    def insight_lead(self, request):
        dto = required_check(
            request.query_params,
            ["date_filter"],
        )
        user = request.query_params.get("user", None)
        mapping = {
            "weekly": get_start_end_week,
            "monthly": get_start_end_month,
            "quarterly": get_current_quarter_range,
            "yearly": get_current_fiscal_year_range,
        }
        res = {"pb": []}
        # {'org':{},"user": User.objects.get(pk=user).get_full_name() if user else user}
        start, end = mapping[dto["date_filter"]](datetime.now())
        org_filter, org_update, org_upsert, org_json = lead_aggregate(
            dto["date_filter"], start, end, None
        )
        res["pb"].append(InsightsLLBSerializer(org_json).data)
        res["lb"] = org_json["lb"]
        filter, update, upsert, json = lead_aggregate(
            dto["date_filter"], start, end, user if user else request.user.id
        )
        res["pb"].append(InsightsLLBSerializer(json).data)
        serialized_json = InsightsLeadSerializer(json if user else org_json).data
        for key in serialized_json:
            res.setdefault(key, [serialized_json.get(key, {})])

        mongo_client = get_db_handle_conn_string()
        db = mongo_client["elixir"]["leads_aggregation"]
        for iteration in range(4):
            start, end = mapping[dto["date_filter"]](start - timedelta(days=1))
            json = db.find_one(
                {
                    "type": dto["date_filter"],
                    "user": user,
                    "date_from": str(start.date()),
                    "date_to": str(end.date()),
                },
                {"_id": 0},
            )
            if not json:
                filter, update, upsert, json = lead_aggregate(dto["date_filter"], start, end, user)
                db.update_one(
                    filter=filter,
                    update=update,
                    upsert=upsert,
                )
            serialized_json = InsightsLeadSerializer(json).data
            for key in serialized_json:
                res[key].append(serialized_json.get(key, {}))

        mongo_client.close()
        return custom_success_response(res)


class InsightProspectViewSet(ModelViewSet):
    queryset = Prospect.objects.all()
    serializer_class = ProspectSerializer
    permission_classes = [IsAuthenticated]

    # http_method_names = ["get", "post"]

    @action(methods=["get"], detail=False)
    def summary_with_recent_prospects(self, request):
        user = int(int(request.query_params.get("user", None)))
        rp = InsightsRecentProspectSerializer(recent_prospects(user), many=True).data
        fiscal_start, fiscal_end = get_current_fiscal_year_range(datetime.now())
        Prospects = Prospect.objects.filter(
            created_at__gte=fiscal_start,
            created_at__lte=fiscal_end,
        ).values("created_at", "closure_time", "is_converted_to_deal", "ageing")
        if user:
            Prospects = Prospects.filter(Q(created_by_id=user) | Q(owner_id=user))
        data = calc_prospect_closure_conversion_rate(Prospects)
        return custom_success_response({"recent_prospects": rp, **data})

    @action(methods=["get"], detail=False)
    def insight_prospect(self, request):
        dto = required_check(
            request.query_params,
            ["date_filter"],
        )
        user = int(request.query_params.get("user", None))
        mapping = {
            "weekly": get_start_end_week,
            "monthly": get_start_end_month,
            "quarterly": get_current_quarter_range,
            "yearly": get_current_fiscal_year_range,
        }
        res = {"pb": []}
        start, end = mapping[dto["date_filter"]](datetime.now())
        org_filter, org_update, org_upsert, org_json = prospect_aggregate(
            dto["date_filter"], start, end, None
        )
        res["pb"].append(InsightsPLBSerializer(org_json).data)
        res["lb"] = org_json["lb"]
        filter, update, upsert, json = prospect_aggregate(
            dto["date_filter"], start, end, user if user else request.user.id
        )
        res["pb"].append(InsightsPLBSerializer(json).data)

        serialized_json = InsightsProspectSerializer(json if user else org_json).data
        for key in serialized_json:
            res.setdefault(key, [serialized_json.get(key, {})])
        mongo_client = get_db_handle_conn_string()
        db = mongo_client["elixir"]["prospects_aggregation"]
        for iteration in range(4):
            start, end = mapping[dto["date_filter"]](start - timedelta(days=1))
            json = db.find_one(
                {
                    "type": dto["date_filter"],
                    "user": user,
                    "date_from": str(start.date()),
                    "date_to": str(end.date()),
                },
                {"_id": 0},
            )
            if not json:
                filter, update, upsert, json = prospect_aggregate(
                    dto["date_filter"], start, end, user
                )
                db.update_one(
                    filter=filter,
                    update=update,
                    upsert=upsert,
                )
            serialized_json = InsightsProspectSerializer(json).data
            for key in serialized_json:
                res[key].append(serialized_json.get(key, {}))
        mongo_client.close()
        return custom_success_response(res)
