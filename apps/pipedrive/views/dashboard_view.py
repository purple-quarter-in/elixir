from datetime import date, datetime, timedelta

from django.db.models import Q
from django.shortcuts import render
from rest_framework.decorators import action
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
from apps.pipedrive.serializers.dashboard_serializer import (
    DashboardLeadSerializer,
    DashboardProspectSerializer,
    DashboardRecentLeadSerializer,
    DashboardRecentProspectSerializer,
)
from elixir.mongo_client import get_db_handle_conn_string
from elixir.utils import (
    custom_success_response,
    get_current_fiscal_year_range,
    get_current_quarter_range,
    get_start_end_month,
    get_start_end_week,
)
from elixir.viewsets import ModelViewSet


def say_hello(request):
    return render(request=request, template_name="email/contact.html")


# Create your views here.
class DashboardLeadViewSet(ModelViewSet):
    queryset = Lead.objects.all()
    serializer_class = LeadSerializer
    permission_classes = [IsAuthenticated]

    # http_method_names = ["get", "post"]

    @action(methods=["get"], detail=False)
    def summary_with_recent_leads(self, request):
        rl = DashboardRecentLeadSerializer(get_recent_leads(request.user.id), many=True).data
        year_now = date.today().year
        fiscal_start, fiscal_end = get_current_fiscal_year_range(datetime.now())
        Leads = (
            Lead.objects.filter(
                created_at__gte=fiscal_start,
                created_at__lte=fiscal_end,
            )
            .filter(Q(created_by=request.user) | Q(owner=request.user))
            .values(
                "created_at",
                "verification_time",
                "closure_time",
                "is_converted_to_prospect",
                "ageing",
            )
        )
        data = calc_lead_verificarion_closure_conversion_rate(Leads)
        return custom_success_response({"recent_leads": rl, **data})

    @action(methods=["get"], detail=False)
    def mydashboard_lead(self, request):
        dto = required_check(
            request.query_params,
            ["date_filter"],
        )
        mapping = {
            "weekly": get_start_end_week,
            "monthly": get_start_end_month,
            "quarterly": get_current_quarter_range,
            "yearly": get_current_fiscal_year_range,
        }
        res = {}
        start, end = mapping[dto["date_filter"]](datetime.now())
        filter, update, upsert, json = lead_aggregate(
            dto["date_filter"], start, end, request.user.id
        )
        serialized_json = DashboardLeadSerializer(json).data
        for key in serialized_json:
            res.setdefault(key, [serialized_json.get(key, {})])
        mongo_client = get_db_handle_conn_string()
        db = mongo_client["elixir"]["leads_aggregation"]
        for iteration in range(4):
            start, end = mapping[dto["date_filter"]](start - timedelta(days=1))
            json = db.find_one(
                {
                    "type": dto["date_filter"],
                    "user": request.user.id,
                    "date_from": str(start.date()),
                    "date_to": str(end.date()),
                },
                {"_id": 0},
            )
            if not json:
                filter, update, upsert, json = lead_aggregate(
                    dto["date_filter"], start, end, request.user.id
                )
                db.update_one(
                    filter=filter,
                    update=update,
                    upsert=upsert,
                )
            serialized_json = DashboardLeadSerializer(json).data
            for key in serialized_json:
                res[key].append(serialized_json.get(key, {}))

        mongo_client.close()
        return custom_success_response(res)


class DashboardProspectViewSet(ModelViewSet):
    queryset = Prospect.objects.all()
    serializer_class = ProspectSerializer
    permission_classes = [IsAuthenticated]

    # http_method_names = ["get", "post"]

    @action(methods=["get"], detail=False)
    def summary_with_recent_prospects(self, request):
        rp = DashboardRecentProspectSerializer(recent_prospects(request.user.id), many=True).data
        year_now = date.today().year
        fiscal_start, fiscal_end = get_current_fiscal_year_range(datetime.now())
        Prospects = (
            Prospect.objects.filter(
                created_at__gte=fiscal_start,
                created_at__lte=fiscal_end,
            )
            .filter(Q(created_by=request.user) | Q(owner=request.user))
            .values("created_at", "closure_time", "is_converted_to_deal", "ageing")
        )
        data = calc_prospect_closure_conversion_rate(Prospects)
        return custom_success_response({"recent_prospects": rp, **data})

    @action(methods=["get"], detail=False)
    def mydashboard_prospect(self, request):
        dto = required_check(
            request.query_params,
            ["date_filter"],
        )
        mapping = {
            "weekly": get_start_end_week,
            "monthly": get_start_end_month,
            "quarterly": get_current_quarter_range,
            "yearly": get_current_fiscal_year_range,
        }
        res = {}
        start, end = mapping[dto["date_filter"]](datetime.now())
        filter, update, upsert, json = prospect_aggregate(
            dto["date_filter"], start, end, request.user.id
        )
        serialized_json = DashboardProspectSerializer(json).data
        for key in serialized_json:
            res.setdefault(key, [serialized_json.get(key, {})])
        mongo_client = get_db_handle_conn_string()
        db = mongo_client["elixir"]["prospects_aggregation"]
        for iteration in range(4):
            start, end = mapping[dto["date_filter"]](start - timedelta(days=1))
            json = db.find_one(
                {
                    "type": dto["date_filter"],
                    "user": request.user.id,
                    "date_from": str(start.date()),
                    "date_to": str(end.date()),
                },
                {"_id": 0},
            )
            if not json:
                filter, update, upsert, json = prospect_aggregate(
                    dto["date_filter"], start, end, request.user.id
                )
                db.update_one(
                    filter=filter,
                    update=update,
                    upsert=upsert,
                )
            serialized_json = DashboardProspectSerializer(json).data
            for key in serialized_json:
                res[key].append(serialized_json.get(key, {}))
        mongo_client.close()
        return custom_success_response(res)
