from datetime import date, datetime, time, timedelta
from math import remainder

import fiscalyear
from dateutil import parser
from dateutil.relativedelta import relativedelta
from django.core.mail import EmailMultiAlternatives
from django.template.loader import get_template
from rest_framework import status
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework.utils.serializer_helpers import ReturnDict, ReturnList


def custom_success_response(
    serialized_data,
    message="success",
    status=status.HTTP_200_OK,
    headers=None,
    cookies=None,
    **kwargs,
):
    data = {}
    data["data"] = serialized_data
    if type(serialized_data) == type([]):
        for key, value in kwargs.items():
            data[key] = value
    elif type(serialized_data) == type({}):
        for key, value in kwargs.items():
            serialized_data[key] = value
    elif type(serialized_data) == ReturnList:
        for key, value in kwargs.items():
            data[key] = value
    elif type(serialized_data) == ReturnDict:
        for key, value in kwargs.items():
            serialized_data[key] = value
    data["message"] = message
    data["status"] = "1"
    response = Response(data, status=status, headers=headers)
    if cookies:
        for key, value in cookies.items():
            response.set_cookie(key, value)
    return response


def custom_send_email(_from, _to, subject, cc, bcc, data, template):
    msg = EmailMultiAlternatives(subject, "", _from, _to, bcc=bcc, cc=cc)
    msg.attach_alternative(get_template(template).render(data), "text/html")
    msg.send(fail_silently=True)


def set_crated_by_updated_by(user):
    return {
        "created_by": user,
        "updated_by": user,
    }


def check_permisson(self, request):
    method = (request.method).lower()
    method = "patch" if method == "put" else method
    if (
        (not request.user.is_superuser)
        and len(self.user_permissions[method]) > 0
        and not request.user.has_perms(tuple(self.user_permissions[method]))
    ):
        raise PermissionDenied()


def sizeof_fmt(num, suffix="B"):
    for unit in ("", "K", "M", "G", "T", "P", "E", "Z"):
        if abs(num) < 1024.0:
            return f"{num:3.1f}{unit}{suffix}"
        num /= 1024.0
    return f"{num:.1f}Yi{suffix}"


def get_start_end_week(dt):
    start_week = dt.replace(hour=0, minute=0, second=0) - timedelta(days=dt.weekday())
    end_week = (start_week + timedelta(days=6)).replace(hour=23, minute=55, second=0)
    return start_week, end_week


def get_start_end_month(dt):
    # The day 28 exists in every month. 4 days later, it's always next month
    next_month = dt.replace(day=28) + timedelta(days=4)
    day_one_month = dt.replace(day=1, hour=0, minute=0)
    last_day_month = (next_month - timedelta(days=next_month.day)).replace(
        hour=23, minute=50, second=0
    )
    # subtracting the number of the current day brings us back one month
    return day_one_month, last_day_month


def get_quarter(date):
    """
    Returns the calendar quarter of `date`
    """
    return 1 + (date.month - 1) // 3


def quarter_start_end(quarter, year=None):
    """
    Returns datetime.daet object for the start
    and end dates of `quarter` for the input `year`
    If `year` is none, it defaults to the current
    year.
    """
    if year is None:
        year = datetime.now().year
    d = datetime(year, 1 + 3 * (quarter - 1), 1)
    return d, d + relativedelta(months=3, days=-1, hour=23, minute=50)


def get_current_quarter_range(date):
    """
    Returns the start and end dates of the current quarter
    before `date`.
    """
    if isinstance(date, str):
        date = parser.parse(date)
    year = date.year
    q = get_quarter(date)
    # logic to handle the first quarter case
    if q == 0:
        q = 4
        year -= 1
    return quarter_start_end(q, year)


def get_current_fiscal_year_range(date):
    """
    Returns the start and end dates of the current fiscal year
    before `date`.
    """
    fy = date.year if date.month in [1, 2, 3] else date.year + 1
    fiscalyear.START_MONTH = 4
    dt = fiscalyear.FiscalYear(fy)

    return dt.start.combine(dt.start.date(), datetime.min.time()), dt.end.combine(
        dt.end.date(), time(hour=23, minute=50, second=0)
    )
