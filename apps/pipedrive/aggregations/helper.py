from datetime import datetime, timedelta

from django.db.models import Q
from rest_framework.exceptions import ValidationError

from apps.pipedrive.models import Lead, Prospect


def required_check(data, keys):
    for x in keys:
        if x not in data:
            raise ValidationError({x: ["this field is required."]})
    return data


def get_recent_leads(
    user_id=None,
    from_date=(datetime.now() - timedelta(days=180)),
    to_date=datetime.now(),
    limit=5,
):
    from_date = datetime.now() - timedelta(days=180)
    to_date = datetime.now()
    leads = Lead.objects.filter(
        created_at__gte=from_date.date(),
        created_at__lte=to_date,
        is_converted_to_prospect=False,
    )
    if user_id:
        leads = leads.filter(Q(created_by_id=user_id) | Q(owner_id=user_id))
    leads = leads.order_by("-created_at")[:limit]
    return leads


# insights & dashboard
def calc_lead_leaderbboard(leads):
    total_leads = leads.count()
    res = {}
    for lead in leads:
        if lead.is_converted_to_prospect:
            owner = lead.ower.get_full_name()
            creater = lead.created_by.get_full_name()
            res.setdefault(owner, 0)
            if owner != creater:
                res[creater] += 1
            res[owner] += 1
    for person in res:
        res[person] = str(round((res[person] / total_leads) * 100, 2))
    return res


def calc_lead_verificarion_closure_conversion_rate(leads):
    res = {"aat": "-", "avt": "-", "act": "-", "lpcr": "-"}
    total_leads = leads.count()
    if total_leads == 0:
        return res
    verification_days, verification_lead_count, closure_days, promoted_count, aging_days = (
        0,
        0,
        0,
        0,
        0,
    )

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
        days = days = (datetime.now().date() - lead["created_at"].date()).days
        if lead["ageing"]:
            days = (lead["ageing"] - lead["created_at"].date()).days
        aging_days += days
    res["aat"] = str(round((aging_days / total_leads), 1))
    res["avt"] = (
        str(round(verification_days / verification_lead_count, 1))
        if verification_lead_count > 0
        else "-"
    )
    res["act"] = str(round(closure_days / promoted_count, 1)) if promoted_count > 0 else "-"
    res["lpcr"] = str(round((promoted_count / total_leads) * 100, 1))
    return res


def recent_prospects(
    user_id=None,
    from_date=(datetime.now() - timedelta(days=180)),
    to_date=datetime.now(),
    limit=5,
):
    from_date = datetime.now() - timedelta(days=180)
    to_date = datetime.now()
    prospects = Prospect.objects.filter(
        created_at__gte=from_date.date(),
        created_at__lte=to_date,
        is_converted_to_deal=False,
    ).select_related("lead")
    if user_id:
        prospects = prospects.filter(Q(created_by_id=user_id) | Q(owner_id=user_id))
    prospects = prospects.order_by("-created_at")[:limit]
    return prospects


def calc_prospect_leaderbboard(prospects):
    total_prospects = prospects.count()
    res = {}
    for prospect in prospects:
        if prospect.is_converted_to_deal:
            owner = prospect.ower.get_full_name()
            creater = prospect.created_by.get_full_name()
            res.setdefault(owner, 0)
            if owner != creater:
                res[creater] += 1
            res[owner] += 1
    for person in res:
        res[person] = str(round((res[person] / total_prospects) * 100, 2))
    return res


def calc_prospect_closure_conversion_rate(prospects):
    res = {"aat": "-", "act": "-", "pdcr": "-"}
    total_prospects = prospects.count()
    if total_prospects == 0:
        return res
    closure_days, promoted_count, aging_days = 0, 0, 0

    for prospect in prospects:
        if prospect["is_converted_to_deal"]:
            promoted_count += 1
        if prospect["closure_time"]:
            closure_days += (prospect["closure_time"].date() - prospect["created_at"].date()).days
        days = days = (datetime.now().date() - prospect["created_at"].date()).days
        if prospect["ageing"]:
            days = (prospect["ageing"] - prospect["created_at"].date()).days
        aging_days += days
    res["aat"] = str(round((aging_days / total_prospects), 1))
    res["act"] = str(round(closure_days / promoted_count, 1)) if promoted_count > 0 else "-"
    res["pdcr"] = str(round((promoted_count / total_prospects) * 100, 1))
    return res
