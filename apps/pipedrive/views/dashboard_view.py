from datetime import date, datetime, timedelta

from django.db.models import Q
from django.shortcuts import render
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated

from apps.pipedrive.aggregations.lead import lead_aggregate
from apps.pipedrive.aggregations.prospect import prospect_aggregate
from apps.pipedrive.models import Lead, Prospect
from apps.pipedrive.serializer import LeadSerializer, ProspectSerializer
from apps.pipedrive.serializers.dashboard_serializer import (
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
    def required_check(self, data, keys):
        for x in keys:
            if x not in data:
                raise ValidationError({x: ["this field is required."]})
        return data

    def recent_leads(
        self,
        user_id,
        from_date=(datetime.now() - timedelta(days=180)),
        to_date=datetime.now(),
        limit=5,
    ):
        from_date = datetime.now() - timedelta(days=180)
        to_date = datetime.now()
        return (
            Lead.objects.filter(
                created_at__gte=from_date.date(),
                created_at__lte=to_date,
                is_converted_to_prospect=False,
            )
            .filter(Q(created_by_id=user_id) | Q(owner_id=user_id))
            .order_by("-created_at")[:limit]
        )

    def calc_lead_verificarion_closure_conversion_rate(self, leads):
        res = {"avt": "-", "act": "-", "lpcr": "-"}
        total_leads = leads.count()
        if total_leads == 0:
            return res
        verification_days, verification_lead_count, closure_days, promoted_count = 0, 0, 0, 0

        for lead in leads:
            if lead["is_converted_to_prospect"]:
                promoted_count += 1
            if lead["closure_time"]:
                closure_days += (lead["closure_time"].date() - lead["created_at"].date()).days
            if lead["verification_time"]:
                verification_lead_count += 1
                verification_days += (
                    lead["verification_time"].date() - lead["created_at"].date()
                ).days

        res["avt"] = (
            str(round(verification_days / verification_lead_count))
            if verification_lead_count > 0
            else "-"
        )
        res["act"] = str(round(closure_days / promoted_count)) if promoted_count > 0 else "-"
        res["lpcr"] = str(round((promoted_count / total_leads) * 100, 1))
        return res

    @action(methods=["get"], detail=False)
    def summary_with_recent_leads(self, request):
        # self.required_check(request.query_params, ["created_at_from", "created_at_to"])
        recent_leads = DashboardRecentLeadSerializer(
            self.recent_leads(request.user.id), many=True
        ).data
        year_now = date.today().year
        fiscal_start = date(year=year_now, month=4, day=1)
        fiscal_end = date(year=year_now + 1, month=3, day=31)
        Leads = (
            Lead.objects.filter(
                created_at__gte=fiscal_start,
                created_at__lte=fiscal_end,
            )
            .filter(Q(created_by=request.user) | Q(owner=request.user))
            .values("created_at", "verification_time", "closure_time", "is_converted_to_prospect")
        )
        data = self.calc_lead_verificarion_closure_conversion_rate(Leads)
        return custom_success_response({"recent_leads": recent_leads, **data})

    @action(methods=["get"], detail=False)
    def mydashboard_lead(self, request):
        dto = self.required_check(
            request.query_params,
            ["date_filter"],
        )
        mapping = {
            "weekly": get_start_end_week,
            "monthly": get_start_end_month,
            "quarterly": get_current_quarter_range,
            "yearly": get_current_fiscal_year_range,
        }
        res = {"status": [], "created": [], "owned": []}
        start, end = mapping[dto["date_filter"]](datetime.now())
        filter, update, upsert, json = lead_aggregate(
            dto["date_filter"], start, end, request.user.id
        )
        res["status"].append(json["status"])
        res["created"].append(json["leads_created"])
        res["owned"].append(json["leads_owned"])
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
                }
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
            res["status"].append(json["status"])
            res["created"].append(json["leads_created"])
            res["owned"].append(json["leads_owned"])
        mongo_client.close()
        return custom_success_response(res)


class DashboardProspectViewSet(ModelViewSet):
    queryset = Prospect.objects.all()
    serializer_class = ProspectSerializer
    permission_classes = [IsAuthenticated]

    # http_method_names = ["get", "post"]
    def required_check(self, data, keys):
        for x in keys:
            if x not in data:
                raise ValidationError({x: ["this field is required."]})
        return data

    def recent_prospects(
        self,
        user_id,
        from_date=(datetime.now() - timedelta(days=180)),
        to_date=datetime.now(),
        limit=5,
    ):
        from_date = datetime.now() - timedelta(days=180)
        to_date = datetime.now()
        return (
            Prospect.objects.filter(
                created_at__gte=from_date.date(),
                created_at__lte=to_date,
                is_converted_to_deal=False,
            )
            .filter(Q(created_by_id=user_id) | Q(owner_id=user_id))
            .select_related("lead")
            .order_by("-created_at")[:limit]
        )

    def calc_prospect_closure_conversion_rate(self, prospects):
        res = {"act": "-", "pdcr": "-"}
        total_prospects = prospects.count()
        if total_prospects == 0:
            return res
        closure_days, promoted_count = 0, 0

        for prospect in prospects:
            if prospect["is_converted_to_deal"]:
                promoted_count += 1
            if prospect["closure_time"]:
                closure_days += (
                    prospect["closure_time"].date() - prospect["created_at"].date()
                ).days
        res["act"] = str(round(closure_days / promoted_count)) if promoted_count > 0 else "-"
        res["pdcr"] = str(round((promoted_count / total_prospects) * 100, 1))
        return res

    @action(methods=["get"], detail=False)
    def summary_with_recent_prospects(self, request):
        # self.required_check(request.query_params, ["created_at_from", "created_at_to"])
        recent_prospects = DashboardRecentProspectSerializer(
            self.recent_prospects(request.user.id), many=True
        ).data
        year_now = date.today().year
        fiscal_start = date(year=year_now, month=4, day=1)
        fiscal_end = date(year=year_now + 1, month=3, day=31)
        Prospects = (
            Prospect.objects.filter(
                created_at__gte=fiscal_start,
                created_at__lte=fiscal_end,
            )
            .filter(Q(created_by=request.user) | Q(owner=request.user))
            .values("created_at", "closure_time", "is_converted_to_deal")
        )
        data = self.calc_prospect_closure_conversion_rate(Prospects)
        return custom_success_response({"recent_prospects": recent_prospects, **data})

    @action(methods=["get"], detail=False)
    def mydashboard_prospect(self, request):
        dto = self.required_check(
            request.query_params,
            ["date_filter"],
        )
        mapping = {
            "weekly": get_start_end_week,
            "monthly": get_start_end_month,
            "quarterly": get_current_quarter_range,
            "yearly": get_current_fiscal_year_range,
        }
        res = {"status": [], "created": [], "owned": []}
        start, end = mapping[dto["date_filter"]](datetime.now())
        filter, update, upsert, json = prospect_aggregate(
            dto["date_filter"], start, end, request.user.id
        )
        res["status"].append(json["status"])
        res["created"].append(json["prospects_created"])
        res["owned"].append(json["prospects_owned"])
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
                }
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
            res["status"].append(json["status"])
            res["created"].append(json["prospects_created"])
            res["owned"].append(json["prospects_owned"])
        mongo_client.close()
        return custom_success_response(res)
