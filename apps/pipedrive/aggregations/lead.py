import imp
from datetime import datetime, timedelta

from django.db.models import Q
from rest_framework.decorators import api_view

from apps.pipedrive.aggregations.helper import (
    calc_lead_verificarion_closure_conversion_rate,
)
from apps.pipedrive.models import Lead
from apps.user.models import User
from elixir.mongo_client import get_db_handle_conn_string
from elixir.schedular import (
    schedule_lead_aggregate_monthly,
    schedule_lead_aggregate_quarterly,
    schedule_lead_aggregate_weekly,
    schedule_lead_aggregate_yearly,
)
from elixir.utils import (
    custom_success_response,
    get_current_fiscal_year_range,
    get_current_quarter_range,
    get_start_end_month,
    get_start_end_week,
)
from elixir.wsgi import Apschedular


@api_view(["POST"])
def lead_aggregate_weekly(request):
    start_week, end_week = get_start_end_week(datetime.now())
    user_ids = User.objects.filter(is_active=True).values_list("id")
    mongo_client = get_db_handle_conn_string()
    db = db = mongo_client["elixir"]["leads_aggregation"]
    for user_id in user_ids:
        filter, update, upsert, json = lead_aggregate(
            "weekly",
            start_week,
            end_week,
            user_id[0],
        )
        db.update_one(
            filter=filter,
            update=update,
            upsert=upsert,
        )
    filter, update, upsert, json = lead_aggregate("weekly", start_week, end_week)
    db.update_one(
        filter=filter,
        update=update,
        upsert=upsert,
    )

    start_week, end_week = get_start_end_week(datetime.now() + timedelta(days=1))
    Apschedular.scheduler.add_job(
        schedule_lead_aggregate_weekly,
        trigger="date",  # Every 10 seconds
        run_date=end_week,
        id="lead_aggregate_weekly",  # The `id` assigned to each job MUST be unique
        max_instances=1,
        replace_existing=True,
    )
    mongo_client.close()
    return custom_success_response({"message": "Lead weekly aggregation done successfully"})


@api_view(["POST"])
def lead_aggregate_monthly(request):
    day_one_month, last_day_month = get_start_end_month(datetime.now())
    user_ids = User.objects.filter(is_active=True).values_list("id")
    mongo_client = get_db_handle_conn_string()
    db = db = mongo_client["elixir"]["leads_aggregation"]
    for user_id in user_ids:
        filter, update, upsert, json = lead_aggregate(
            "monthly",
            day_one_month,
            last_day_month,
            user_id[0],
        )
        db.update_one(
            filter=filter,
            update=update,
            upsert=upsert,
        )
    filter, update, upsert, json = lead_aggregate("monthly", day_one_month, last_day_month)
    db.update_one(
        filter=filter,
        update=update,
        upsert=upsert,
    )
    day_one_month, last_day_month = get_start_end_month(datetime.now() + timedelta(days=1))
    Apschedular.scheduler.add_job(
        schedule_lead_aggregate_monthly,
        trigger="date",  # Every 10 seconds
        run_date=last_day_month,
        id="lead_aggregate_monthly",  # The `id` assigned to each job MUST be unique
        max_instances=1,
        replace_existing=True,
    )
    mongo_client.close()
    return custom_success_response({"message": "Lead monthly aggregation done successfully"})


@api_view(["POST"])
def lead_aggregate_quarterly(request):
    day_one_quarter, last_day_quarter = get_current_quarter_range(datetime.now())
    user_ids = User.objects.filter(is_active=True).values_list("id")
    mongo_client = get_db_handle_conn_string()
    db = db = mongo_client["elixir"]["leads_aggregation"]
    for user_id in user_ids:
        filter, update, upsert, json = lead_aggregate(
            "quarterly",
            day_one_quarter,
            last_day_quarter,
            user_id[0],
        )
        db.update_one(
            filter=filter,
            update=update,
            upsert=upsert,
        )
    filter, update, upsert, json = lead_aggregate("quarterly", day_one_quarter, last_day_quarter)
    db.update_one(
        filter=filter,
        update=update,
        upsert=upsert,
    )
    day_one_quarter, last_day_quarter = get_current_quarter_range(
        datetime.now() + timedelta(days=1)
    )
    Apschedular.scheduler.add_job(
        schedule_lead_aggregate_quarterly,
        trigger="date",  # Every 10 seconds
        run_date=last_day_quarter,
        id="lead_aggregate_quarterly",  # The `id` assigned to each job MUST be unique
        max_instances=1,
        replace_existing=True,
    )
    mongo_client.close()
    return custom_success_response({"message": "Lead quarterly aggregation done successfully"})


@api_view(["POST"])
def lead_aggregate_yearly(request):
    day_one_fiscal_year, last_day_fiscal_year = get_current_fiscal_year_range(datetime.now())
    user_ids = User.objects.filter(is_active=True).values_list("id")
    mongo_client = get_db_handle_conn_string()
    db = db = mongo_client["elixir"]["leads_aggregation"]
    for user_id in user_ids:
        filter, update, upsert, json = lead_aggregate(
            "yearly",
            day_one_fiscal_year,
            last_day_fiscal_year,
            user_id[0],
        )
        db.update_one(
            filter=filter,
            update=update,
            upsert=upsert,
        )
    filter, update, upsert, json = lead_aggregate(
        "yearly",
        day_one_fiscal_year,
        last_day_fiscal_year,
    )
    db.update_one(
        filter=filter,
        update=update,
        upsert=upsert,
    )
    day_one_fiscal_year, last_day_fiscal_year = get_current_fiscal_year_range(
        datetime.now() + timedelta(days=1)
    )
    Apschedular.scheduler.add_job(
        schedule_lead_aggregate_yearly,
        trigger="date",  # Every 10 seconds
        run_date=last_day_fiscal_year,
        id="lead_aggregate_yearly",  # The `id` assigned to each job MUST be unique
        max_instances=1,
        replace_existing=True,
    )
    mongo_client.close()
    return custom_success_response({"message": "Lead yearly aggregation done successfully"})


def lead_aggregate(type, date_from, date_to, user_id=None):
    user_name = User.objects.get(pk=user_id).get_full_name() if user_id else "Purple Quarter"
    leads = Lead.objects.filter(created_at__gte=date_from, created_at__lte=date_to).values(
        "status",
        "created_by_id",
        "owner_id",
        "is_converted_to_prospect",
        "source",
        "verification_time",
        "closure_time",
        "created_at",
        "ageing",
    )
    if user_id:
        leads = leads.filter(Q(created_by_id=user_id) | Q(owner_id=user_id))
    status = {
        "Unverified": 0,
        "Verified": 0,
        "Lost": 0,
        "Junk": 0,
        "Deferred": 0,
    }
    inbound_source = {"Referral": 0, "LinkedIn": 0, "Social Media": 0}
    outbound_source = {
        "Events": 0,
        "Email Campaign": 0,
        "LinkedIn": 0,
        "Hoardings/Billboards": 0,
        "RA/BDA": 0,
        "VC/PE": 0,
        "Lead Gen Partner": 0,
    }
    leads_created = 0
    leads_owned = 0
    total_leads = leads.count()
    lptp = 0
    lead_v_c_c = calc_lead_verificarion_closure_conversion_rate(leads)
    leaderboard = {}
    lb = []
    for lead in leads:
        # status
        status[lead["status"]] += 1
        # converted to prospect
        if lead["is_converted_to_prospect"] == 1:
            lptp += 1
        # inbound outbound lead
        if lead["source"] == "LinkedIn":
            if lead["created_by_id"] == None:
                inbound_source[lead["source"]] += 1
            else:
                outbound_source[lead["source"]] += 1
        elif lead["source"] in inbound_source:
            inbound_source[lead["source"]] += 1
        elif lead["source"] in outbound_source:
            outbound_source[lead["source"]] += 1

        if user_id:
            if lead["created_by_id"] == user_id:
                leads_created += 1
            if lead["owner_id"] == user_id:
                leads_owned += 1
        else:
            leads_created = total_leads
            leads_owned = total_leads
        ## calc  lead leaderboard
        if not user_id:
            owner = lead["owner_id"]
            creater = lead["created_by_id"]
            if owner and owner not in leaderboard:
                leaderboard.setdefault(
                    owner,
                    {
                        "created_owned": 0,
                        "promoted": 0,
                        "rate": 0,
                        "name": User.objects.get(pk=lead["owner_id"]).get_full_name(),
                        "created": 0,
                        "owned": 0,
                    },
                )
            if creater and creater not in leaderboard:
                leaderboard.setdefault(
                    creater,
                    {
                        "created_owned": 0,
                        "promoted": 0,
                        "rate": 0,
                        "name": User.objects.get(pk=lead["created_by_id"]).get_full_name(),
                        "created": 0,
                        "owned": 0,
                    },
                )
            if owner:
                leaderboard[owner]["owned"] += 1
            if creater:
                leaderboard[creater]["created"] += 1
            if owner != creater:
                if owner:
                    leaderboard[owner]["created_owned"] += 1
                    if lead["is_converted_to_prospect"]:
                        leaderboard[owner]["promoted"] += 1
                if creater:
                    leaderboard[creater]["created_owned"] += 1
                    if lead["is_converted_to_prospect"]:
                        leaderboard[creater]["promoted"] += 1
            else:
                if owner:
                    leaderboard[owner]["created_owned"] += 1
                    if lead["is_converted_to_prospect"]:
                        leaderboard[owner]["promoted"] += 1
                elif creater:
                    leaderboard[creater]["created_owned"] += 1
                    if lead["is_converted_to_prospect"]:
                        leaderboard[creater]["promoted"] += 1
    if not user_id:
        for person in leaderboard:
            leaderboard[person]["rate"] = str(
                round(
                    (leaderboard[person]["promoted"] / leaderboard[person]["created_owned"]) * 100,
                    2,
                )
            )
            lb.append(leaderboard[person])
    filter = {
        "type": type,
        "user": user_id,
        "date_from": str(date_from.date()),
        "date_to": str(date_to.date()),
    }

    update = {
        "$set": {
            "user_name": user_name,
            "status": status,
            "created": leads_created,
            "owned": leads_owned,
            "total_leads": total_leads,
            "lptp": lptp,
            "inbound_source": inbound_source,
            "outbound_source": outbound_source,
            "lb": lb,
            **lead_v_c_c,
        }
    }

    upsert = True
    return filter, update, upsert, update["$set"]
