from datetime import datetime, timedelta
from math import remainder

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
    for unit in ("", "Ki", "Mi", "Gi", "Ti", "Pi", "Ei", "Zi"):
        if abs(num) < 1024.0:
            return f"{num:3.1f}{unit}{suffix}"
        num /= 1024.0
    return f"{num:.1f}Yi{suffix}"
