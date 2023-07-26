from math import remainder
from rest_framework import status
from rest_framework.response import Response
from django.core.mail import EmailMultiAlternatives
from django.template.loader import get_template

def custom_success_response(
    serialized_data,
    message="success",
    status=status.HTTP_200_OK,
    headers=None,
    **kwargs,
):
    data = {}
    data["data"] = serialized_data
    if type(serialized_data).__name__ == "list":
        for key, value in kwargs.items():
            data[key] = value
    else:
        for key, value in kwargs.items():
            serialized_data[key] = value
    data["message"] = message
    data["status"] = "1"
    return Response(data, status=status, headers=headers)

def custom_send_email(_from,_to,subject,cc,bcc,data,template):
    msg = EmailMultiAlternatives(subject, "", _from, _to,bcc=bcc,cc=cc)
    msg.attach_alternative(get_template(template).render(data), "text/html")
    msg.send(fail_silently=True)