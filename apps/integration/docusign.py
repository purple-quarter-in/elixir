import base64
from datetime import datetime, timedelta

import requests
from django.conf import settings
from rest_framework.decorators import api_view
from rest_framework.exceptions import ValidationError

from apps.integration.models import Integration
from apps.pipedrive.models import ServiceContract
from elixir.schedular import schedule_refresh_docusign_token
from elixir.utils import custom_success_response
from elixir.wsgi import Apschedular

DOCUSIGN_INTEGRATION_KEY = settings.DOCUSIGN_INTEGRATION_KEY
DOCUSIGN_SECRET_KEY = settings.DOCUSIGN_SECRET_KEY
DOCUSIGN_DOMAIN = settings.DOCUSIGN_DOMAIN


def encode_base64(data):
    return base64.b64encode(data.encode("utf-8"))


def _get_refresh_access_token(code):
    url = f"{DOCUSIGN_DOMAIN}/oauth/token"
    json = {"grant_type": "authorization_code", "code": code}
    headers = {
        "Authorization": f"Basic {encode_base64(f'{DOCUSIGN_INTEGRATION_KEY}:{DOCUSIGN_SECRET_KEY}').decode('utf-8')}"
    }
    response = requests.post(url, json=json, headers=headers)
    return response.json()


def _get_user_auth_info(access_token):
    url = f"{DOCUSIGN_DOMAIN}/oauth/userinfo"
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(url, headers=headers)
    return response.json()


def create_envelop(service_contract):
    integration_docusign = Integration.objects.filter(
        service_name="docusign", archived=False
    ).last()
    if not integration_docusign:
        raise ValidationError({"integration": ["Doccusign integration required!!!"]})
    account_info = integration_docusign.userinfo["accounts"][0]
    url = (
        f"{account_info['base_uri']}/restapi/v2.1/accounts/{account_info['account_id']}/envelopes/"
    )
    pdf = service_contract.file.open("rb")
    """
    write logic to base64 pdf document and create json body
    """
    json = {
        "documents": [
            {
                "documentID": service_contract.id,
                "name": service_contract.file_name,
                "documentBase64": base64.b64encode(pdf.read()).decode("utf-8"),
            }
        ]
    }
    headers = {"Authorization": f"Bearer {integration_docusign.access_token}"}
    response = requests.post(url, headers=headers, json=json)
    return response.json()


def get_document_status(service_contract):
    integration_docusign = Integration.objects.filter(
        service_name="docusign", archived=False
    ).last()
    if not integration_docusign:
        raise ValidationError({"integration": "Docusign integration required!!!"})
    account_info = integration_docusign.userinfo["accounts"][0]
    url = f"{account_info['base_uri']}/restapi/v2.1/accounts/{account_info['account_id']}{service_contract.docusign.file_url}"

    headers = {"Authorization": f"Bearer {integration_docusign.access_token}"}
    response = requests.get(url, headers=headers)
    return response.json()


def view_document(service_contract):
    integration_docusign = Integration.objects.filter(
        service_name="docusign", archived=False
    ).last()
    if not integration_docusign:
        raise ValidationError({"integration": ["Doccusign integration required!!!"]})
    account_info = integration_docusign.userinfo["accounts"][0]
    url = f"{account_info['base_uri']}/restapi/v2.1/accounts/{account_info['account_id']}{service_contract.docusign.file_url}/documents/{service_contract.id}"

    headers = {"Authorization": f"Bearer {integration_docusign.access_token}"}
    response = requests.get(url, headers=headers)
    return response.content


def _refresh_token_token(instance):
    url = f"{DOCUSIGN_DOMAIN}/oauth/token"
    json = {"grant_type": "refresh_token", "refresh_token": instance.refresh_token}
    headers = {
        "Authorization": f"Basic {encode_base64(f'{DOCUSIGN_INTEGRATION_KEY}:{DOCUSIGN_SECRET_KEY}').decode('utf-8')}"
    }
    response = requests.post(url, json=json, headers=headers)
    return response.json()


@api_view(["POST"])
def refresh_access_token(request):
    integration_docusign = Integration.objects.get(pk=request.data.get("instance"))
    docusign_access = _refresh_token_token(integration_docusign)
    integration_docusign.access_token = docusign_access["access_token"]
    integration_docusign.refresh_token = docusign_access["refresh_token"]
    integration_docusign.token_type = docusign_access["token_type"]
    integration_docusign.expiry = datetime.now() + timedelta(seconds=docusign_access["expires_in"])
    integration_docusign.save()
    Apschedular.scheduler.add_job(
        schedule_refresh_docusign_token,
        trigger="date",
        run_date=integration_docusign.expiry - timedelta(minutes=5),
        id=f"docusign-refresh-access-token",
        max_instances=1,
        kwargs={
            "instance": integration_docusign.id,
        },
        replace_existing=True,
    )
    return custom_success_response({"messsage": "docusign integration refreshed successfully"})


@api_view(["GET"])
def oauth(request, *args, **kwargs):
    """
    get code after authorization
    call requests to docusign Api for access and refresh token.
    call requests to get account details of user
    start a schedular to refessh token 5 mins before expiry
    """
    if "code" in request.query_params:
        code = request.query_params.get("code")
        old_integration = Integration.objects.filter(
            service_name="docusign", archived=False
        ).last()
        if old_integration:
            old_integration.archived = True
            old_integration.save()
        docusign_access = _get_refresh_access_token(code)
        docusign_userinfo = _get_user_auth_info(docusign_access["access_token"])
        integration = Integration.objects.create(
            service_name="docusign",
            auth_type="oauth2",
            user_email=docusign_userinfo["email"],
            access_token=docusign_access["access_token"],
            refresh_token=docusign_access["refresh_token"],
            token_type=docusign_access["token_type"],
            expiry=datetime.now() + timedelta(seconds=docusign_access["expires_in"]),
            userinfo=docusign_userinfo,
        )
        Apschedular.scheduler.add_job(
            schedule_refresh_docusign_token,
            trigger="date",
            run_date=integration.expiry - timedelta(minutes=5),
            id=f"docusign-refresh-access-token",
            max_instances=1,
            kwargs={
                "instance": integration.id,
            },
            replace_existing=True,
        )
    else:
        raise ValidationError({"code": "Uthorizatin failed"})
    return custom_success_response({"code": request.query_params.get("code")})


@api_view(["POST"])
def listen_event(request, *args, **kwargs):
    data = request.data["data"]
    accountId = data["accountId"]
    envelopeId = data["envelopeId"]
    integration = Integration.objects.filter(service_name="docusign", archived=False).last()
    if integration:
        sc = (
            ServiceContract.objects.filter(docusign__envelop_id=envelopeId)
            .select_related("docusign")
            .last()
        )
        sc.status = data["envelopeSummary"]["status"]
        sc.docusign.status = data["envelopeSummary"]["status"]
        sc.event_date = data["envelopeSummary"]["statusChangedDateTime"]
        sc.docusign.save()
        sc.save()
    return custom_success_response({"message": "event captured successfully"})
