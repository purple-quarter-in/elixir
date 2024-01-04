from datetime import datetime, timedelta
from urllib.parse import uses_relative

from django.db.models import Q
from rest_framework.decorators import api_view

from apps.pipedrive.aggregations.helper import calc_prospect_closure_conversion_rate
from apps.pipedrive.models import Prospect
from apps.user.models import User
from elixir.mongo_client import get_db_handle_conn_string
from elixir.schedular import (
    schedule_prospect_aggregate_monthly,
    schedule_prospect_aggregate_quarterly,
    schedule_prospect_aggregate_weekly,
    schedule_prospect_aggregate_yearly,
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
def prospect_aggregate_weekly(request):
    start_week, end_week = get_start_end_week(datetime.now())
    user_ids = User.objects.filter(is_active=True).values_list("id")
    mongo_client = get_db_handle_conn_string()
    db = db = mongo_client["elixir"]["prospects_aggregation"]
    for user_id in user_ids:
        filter, update, upsert, json = prospect_aggregate(
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
        schedule_prospect_aggregate_weekly,
        trigger="date",  # Every 10 seconds
        run_date=end_week,
        id="prospect_aggregate_weekly",  # The `id` assigned to each job MUST be unique
        max_instances=1,
        replace_existing=True,
    )
    mongo_client.close()
    return custom_success_response({"message": "prospect weekly aggregation done successfully"})


@api_view(["POST"])
def prospect_aggregate_monthly(request):
    day_one_month, last_day_month = get_start_end_month(datetime.now())
    user_ids = User.objects.filter(is_active=True).values_list("id")
    mongo_client = get_db_handle_conn_string()
    db = db = mongo_client["elixir"]["prospects_aggregation"]
    for user_id in user_ids:
        filter, update, upsert, json = prospect_aggregate(
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
        schedule_prospect_aggregate_monthly,
        trigger="date",  # Every 10 seconds
        run_date=last_day_month,
        id="prospect_aggregate_monthly",  # The `id` assigned to each job MUST be unique
        max_instances=1,
        replace_existing=True,
    )
    mongo_client.close()
    return custom_success_response({"message": "prospect monthly aggregation done successfully"})


@api_view(["POST"])
def prospect_aggregate_quarterly(request):
    day_one_quarter, last_day_quarter = get_current_quarter_range(datetime.now())
    user_ids = User.objects.filter(is_active=True).values_list("id")
    mongo_client = get_db_handle_conn_string()
    db = db = mongo_client["elixir"]["prospects_aggregation"]
    for user_id in user_ids:
        filter, update, upsert, json = prospect_aggregate(
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
        schedule_prospect_aggregate_quarterly,
        trigger="date",  # Every 10 seconds
        run_date=last_day_quarter,
        id="prospect_aggregate_quarterly",  # The `id` assigned to each job MUST be unique
        max_instances=1,
        replace_existing=True,
    )
    mongo_client.close()
    return custom_success_response({"message": "prospect quarterly aggregation done successfully"})


@api_view(["POST"])
def prospect_aggregate_yearly(request):
    day_one_fiscal_year, last_day_fiscal_year = get_current_fiscal_year_range(datetime.now())
    user_ids = User.objects.filter(is_active=True).values_list("id")
    mongo_client = get_db_handle_conn_string()
    db = db = mongo_client["elixir"]["prospects_aggregation"]
    for user_id in user_ids:
        filter, update, upsert, json = prospect_aggregate(
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
        schedule_prospect_aggregate_yearly,
        trigger="date",  # Every 10 seconds
        run_date=last_day_fiscal_year,
        id="prospect_aggregate_yearly",  # The `id` assigned to each job MUST be unique
        max_instances=1,
        replace_existing=True,
    )
    mongo_client.close()
    return custom_success_response({"message": "prospect yearly aggregation done successfully"})


def prospect_aggregate(type, date_from, date_to, user_id=None):
    user_name = User.objects.get(pk=user_id).get_full_name() if user_id else "Purple Quarter"

    prospects = Prospect.objects.filter(created_at__gte=date_from, created_at__lte=date_to).values(
        "status",
        "created_by_id",
        "owner_id",
        "closure_time",
        "is_converted_to_deal",
        "created_at",
        "ageing",
    )
    if user_id:
        prospects = prospects.filter(Q(created_by_id=user_id) | Q(owner_id=user_id))
    status = {
        "Qualified": 0,
        "Disqualified": 0,
        "Lost": 0,
        "Deferred": 0,
    }
    prospects_created = 0
    prospects_owned = 0
    pptd = 0
    total_prospects = prospects.count()
    prospect_c_c = calc_prospect_closure_conversion_rate(prospects)
    leaderboard = {}
    lb = []
    for prospect in prospects:
        status[prospect["status"]] += 1
        # converted to prospect
        if prospect["is_converted_to_deal"] == 1:
            pptd += 1
        if user_id:
            if prospect["created_by_id"] == user_id:
                prospects_created += 1
            if prospect["owner_id"] == user_id:
                prospects_owned += 1
        else:
            prospects_created = total_prospects
            prospects_owned = total_prospects

        ## calc  prospect leaderboard
        if not user_id:
            owner = prospect["owner_id"]
            creater = prospect["created_by_id"]
            if owner and owner not in leaderboard:
                leaderboard.setdefault(
                    owner,
                    {
                        "created_owned": 0,
                        "converted": 0,
                        "rate": 0,
                        "name": User.objects.get(pk=prospect["owner_id"]).get_full_name(),
                    },
                )
            if creater:
                leaderboard.setdefault(
                    creater,
                    {
                        "created_owned": 0,
                        "converted": 0,
                        "rate": 0,
                        "name": User.objects.get(pk=prospect["created_by_id"]).get_full_name(),
                    },
                )

            if owner != creater:
                if owner:
                    leaderboard[owner]["created_owned"] += 1
                    leaderboard[owner]["created_owned"] += 1
                    if prospect["is_converted_to_deal"]:
                        leaderboard[owner]["converted"] += 1
                if creater:
                    leaderboard[creater]["created_owned"] += 1
                    leaderboard[creater]["created_owned"] += 1
                    if prospect["is_converted_to_deal"]:
                        leaderboard[creater]["converted"] += 1
            else:
                if owner:
                    leaderboard[owner]["created_owned"] += 1
                    leaderboard[owner]["created_owned"] += 1
                    if prospect["is_converted_to_deal"]:
                        leaderboard[owner]["converted"] += 1
                elif creater:
                    leaderboard[creater]["created_owned"] += 1
                    leaderboard[creater]["created_owned"] += 1
                    if prospect["is_converted_to_deal"]:
                        leaderboard[creater]["converted"] += 1
    if not user_id:
        for person in leaderboard:
            leaderboard[person]["rate"] = str(
                round(
                    (leaderboard[person]["converted"] / leaderboard[person]["created_owned"])
                    * 100,
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
            "created": prospects_created,
            "owned": prospects_owned,
            "pptd": pptd,
            "total_prospects": total_prospects,
            "lb": lb,
            **prospect_c_c,
        }
    }
    upsert = True
    return filter, update, upsert, update["$set"]
