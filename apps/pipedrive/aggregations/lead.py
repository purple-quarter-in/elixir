import imp
from datetime import datetime, timedelta

from django.db.models import Q
from rest_framework.decorators import api_view

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


def lead_aggregate(type, date_from, date_to, user_id):
    leads = (
        Lead.objects.filter(created_at__gte=date_from, created_at__lte=date_to)
        .filter(Q(created_by_id=user_id) | Q(owner_id=user_id))
        .values("status", "created_by_id", "owner_id")
    )
    status = {
        "Unverified": 0,
        "Verified": 0,
        "Lost": 0,
        "Junk": 0,
        "Deferred": 0,
    }
    leads_created = 0
    leads_owned = 0
    for lead in leads:
        status[lead["status"]] += 1
        if lead["created_by_id"] == user_id:
            leads_created += 1
        if lead["owner_id"] == user_id:
            leads_owned += 1
    json = {
        "type": type,
        "user": user_id,
        "date_from": str(date_from.date()),
        "date_to": str(date_to.date()),
        "status": status,
        "leads_created": leads_created,
        "leads_owned": leads_owned,
    }

    filter = {
        "type": type,
        "user": user_id,
        "date_from": str(date_from.date()),
        "date_to": str(date_to.date()),
    }

    update = {
        "$set": {"status": status, "leads_created": leads_created, "leads_owned": leads_owned}
    }
    upsert = True
    return filter, update, upsert, json
