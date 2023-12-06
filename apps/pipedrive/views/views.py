import base64
import os
from datetime import date, datetime
from urllib import request

from django.http import HttpResponse
from django.shortcuts import render
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.generics import CreateAPIView
from rest_framework.permissions import IsAuthenticated
from yaml import serialize

from apps.client.models import Contact, Organisation
from apps.integration.docusign import create_envelop, view_document
from apps.integration.slack import slack_send_message
from apps.notification.models import Notification
from apps.pipedrive.models import (
    Deal,
    Lead,
    Prospect,
    RDCapsule,
    RoleDetail,
    ServiceContract,
    ServiceContractDocuSignDetail,
    ServiceProposal,
)
from apps.pipedrive.serializer import (
    CreateLeadSerializer,
    DealSerializer,
    LeadSerializer,
    ProspectSerializer,
    RDCapsuleSerializer,
    RoleDetailSerializer,
    ServiceContractSerializer,
    ServiceProposalSerializer,
    UpdateDealSerializer,
    UpdateLeadSerializer,
    UpdateProspectSerializer,
)
from elixir.changelog import changelog
from elixir.settings.base import BASE_DIR
from elixir.utils import (
    check_permisson,
    custom_success_response,
    set_crated_by_updated_by,
)
from elixir.viewsets import ModelViewSet


def contact_import(request):
    # fp_write = open(os.path.join(BASE_DIR, "logg.txt"), "w+")
    contact_list = []
    for fp in open(os.path.join(BASE_DIR, "data/contact_import.tsv"), "r"):
        row = fp.split("\t")
        # fp_write.write(str(len(row)) + " " + str(row[0]) + "\n")
        if not Organisation.objects.filter(name=row[0]).exists():
            org = Organisation.objects.update_or_create(
                name=row[0], defaults={"created_by_id": row[8], "updated_by_id": row[8]}
            )
            # designation  & email cant be empty
            contact_list.append(
                Contact(
                    organisation_id=org[0].id,
                    name=row[1],
                    email=row[2],
                    std_code=row[3],
                    phone=row[4],
                    designation=row[5],
                    type=row[6],
                    created_by_id=row[8],
                    updated_by_id=row[8],
                )
            )
        else:
            contact_list.append(
                Contact(
                    organisation_id=Organisation.objects.get(name=row[0]).id,
                    name=row[1],
                    email=row[2],
                    std_code=row[3],
                    phone=row[4],
                    designation=row[5],
                    type=row[6],
                    created_by_id=row[8],
                    updated_by_id=row[8],
                )
            )
            print(row[0])
    Contact.objects.bulk_create(contact_list)
    return custom_success_response({})


def org_import(request):
    # fp_write = open(os.path.join(BASE_DIR, "logg.txt"), "w+")
    org_list = []
    for fp in open(os.path.join(BASE_DIR, "data/org_import.tsv"), "r"):
        row = fp.split("\t")
        # fp_write.write(str(len(row)) + " " + str(row[0]) + "\n")
        if not Organisation.objects.filter(name=row[0]).exists():
            print(row[0])
            org_list.append(
                Organisation(
                    name=row[0],
                    industry=row[4],
                    domain=row[5],
                    created_by_id=row[9],
                    updated_by_id=row[9],
                    created_at=row[8],
                )
            )
    Organisation.objects.bulk_create(org_list)
    return custom_success_response({})


x = {
    "organisation": {
        "id": 1,
        "name": "",
        "contact_details": [
            {
                "name": "",
                "email": "",
                "std_code": "",
                "phone": "",
                "designation": "",
                "type": "",
            }
        ],
    },
    "role_details": {"region": "" "role_type" "budget_range"},
    "source": "",
}


# Create your views here.
class LeadViewSet(ModelViewSet):
    queryset = (
        Lead.objects.select_related(
            "created_by",
            "updated_by",
            "owner",
            "fullfilled_by",
            "closed_by",
            "organisation",
            "role",
        )
        .prefetch_related("organisation__contact_organisation")
        .filter(is_converted_to_prospect=False)
        .order_by("-created_at")
    )
    serializer_class = LeadSerializer
    permission_classes = [IsAuthenticated]
    filtering = {
        "title": {"operation": "contains", "lookup": "__icontains"},
        "role__region": {"operation": "in", "lookup": "__in"},
        "source": {"operation": "in", "lookup": "__in"},
        "status": {"operation": "in", "lookup": "__in"},
        "owner": {"operation": "in", "lookup": "_id__in"},
        "created_by": {"operation": "in", "lookup": "_id__in"},
        "created_at_from": {"operation": "from_to", "lookup": "__gte"},
        "created_at_to": {"operation": "from_to", "lookup": "__lte"},
    }
    sorting = ["created_at"]
    pagination = True
    user_permissions = {
        "get": ["pipedrive.view_lead"],
        "post": ["pipedrive.add_lead"],
        "patch": ["pipedrive.change_lead"],
    }
    changelog = {
        "model": "Lead",
        "mapping_obj": "id",
        "is_mapping_obj_func": False,
        "create": {
            "is_created": {"type": "Entity Created", "description": "Lead Created"},
        },
        "update": {
            "status": {"type": "Status Update", "description": "Lead State Updated"},
            "is_converted_to_prospect": {
                "type": "State Update",
                "description": "Lead Converted to Prospect",
            },
            "service_fee": {
                "type": "Field Update",
                "description": "Service Fee Updated",
            },
            "flat_fee": {
                "type": "Field Update",
                "description": "Flat Fee Updated",
            },
            "equity_fee": {
                "type": "Field Update",
                "description": "Equity Fee Updated",
            },
            "owner": {
                "field_to_get": "get_full_name",
                "type": "Field Update",
                "description": "Owned by Field Updated",
            },
            "closed_by": {
                "field_to_get": "get_full_name",
                "type": "Field Update",
                "description": "Closed by Field Updated",
            },
            "fullfilled_by": {
                "field_to_get": "get_full_name",
                "type": "Field Update",
                "description": "Fullfilled by Field Updated",
            },
        },
    }

    def create(self, request, *args, **kwargs):
        check_permisson(self, request)
        serializer = CreateLeadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        dto = request.data
        org_id = None
        role_serializer = RoleDetailSerializer(data=dto["role_details"])
        role_serializer.is_valid(raise_exception=True)
        if "id" in dto["organisation"]:
            # case of update
            org_id = dto["organisation"]["id"]
            if "contact_details" in dto["organisation"]:
                for contact in dto["organisation"]["contact_details"]:
                    Contact.objects.create(
                        organisation_id=org_id,
                        **contact,
                        **set_crated_by_updated_by(request.user),
                    )
        elif "id" not in dto["organisation"] and "name" in dto["organisation"]:
            # case of create
            if Organisation.objects.filter(name__iexact=dto["organisation"]["name"]).exists():
                raise ValidationError(
                    {
                        "already_exists": [
                            f'Organisation with name {dto["organisation"]["name"]} already exists'
                        ]
                    }
                )
            org = Organisation.objects.create(
                name=dto["organisation"]["name"],
                created_by=request.user,
                updated_by=request.user,
            )
            changelog(
                {
                    "model": "Organisation",
                    "mapping_obj": "id",
                    "is_mapping_obj_func": False,
                    "create": {
                        "is_created": {
                            "type": "Entity Created",
                            "description": "Account Created",
                        },
                    },
                },
                org,
                {"is_created": request.user},
                "create",
                request.user.id,
            )
            org_id = org.id
            if "contact_details" in dto["organisation"]:
                for contact in dto["organisation"]["contact_details"]:
                    Contact.objects.create(
                        organisation_id=org_id,
                        **contact,
                        **set_crated_by_updated_by(request.user),
                    )
            pass
        role = role_serializer.save()
        lead = Lead.objects.create(
            organisation_id=org_id,
            role=role,
            source=dto["source"],
            title=dto["title"],
            created_by=request.user,
            updated_by=request.user,
            owner=request.user,
        )
        changelog(
            self.changelog,
            lead,
            {"is_created": request.user},
            "create",
            request.user.id,
        )
        return custom_success_response(
            {"message": "Lead created Successfully"}, status=status.HTTP_201_CREATED
        )

    @action(detail=True, methods=["patch"])
    def promote(self, request, pk):
        check_permisson(self, request)
        obj = self.get_object()
        if obj.is_converted_to_prospect:
            raise ValidationError({"message": ["Lead already converted to prospect"]})
        obj.is_converted_to_prospect = True
        obj.updated_by = request.user
        prospect = Prospect.objects.update_or_create(
            lead=obj,
            defaults={"owner": obj.owner, **set_crated_by_updated_by(request.user)},
        )
        if prospect:
            changelog(
                self.changelog,
                obj,
                {"is_converted_to_prospect": True},
                "update",
                request.user.id,
            )
            if not obj.closure_time:
                obj.closure_time = datetime.now()
            obj.save()
            return custom_success_response(self.serializer_class(obj).data)
        else:
            raise ValidationError({"message": ["Technical error"]})

    @action(detail=False, methods=["patch"])
    def bulk_archive(self, request):
        check_permisson(self, request)
        if "leads" not in request.data:
            raise ValidationError({"leads": "List of lead id is required"})
        if "archive" not in request.data:
            raise ValidationError({"archive": "This boolean field is required"})

        prospect = Lead.objects.filter(id__in=request.data.get("leads")).update(
            archived=request.data.get("archive")
        )
        if prospect > 0:
            return custom_success_response(
                {"message": [f"{prospect} prospect(s) has been archived"]}
            )
        else:
            raise ValidationError({"message": ["Technical error"]})

    def partial_update(self, request, pk):
        check_permisson(self, request)
        lead = Lead.objects.get(id=pk)
        serializer = UpdateLeadSerializer(lead, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        if self.changelog and ("update" in self.changelog):
            changelog(
                self.changelog,
                lead,
                serializer._validated_data,
                "update",
                request.user.id,
            )
        if (
            "owner" in serializer._validated_data
            and lead.owner_id != serializer._validated_data["owner"].id
        ):
            Notification.objects.create(
                type="Lead Owner Assigned",
                description=f"{request.user.get_full_name()} assigned Ownership for Lead {lead.title} to {serializer.validated_data['owner'].get_full_name()}",
                user=serializer.validated_data["owner"],
                model_name="Lead",
                object_id=lead.id,
            )
        if (
            not lead.verification_time
            and "status" in serializer.validated_data
            and serializer.validated_data["status"] != "Unverified"
        ):
            serializer.save(updated_by=request.user, verification_time=datetime.now())
        else:
            serializer.save(updated_by=request.user)
        return custom_success_response(serializer.data, status=status.HTTP_200_OK)


class RoleDetailViewSet(ModelViewSet):
    queryset = RoleDetail.objects.all()
    serializer_class = RoleDetailSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ["get", "patch"]
    changelog = {
        "model": "Lead",
        "mapping_obj": "get_lead_id",
        "is_mapping_obj_func": True,
        "update": {
            "location": {
                "type": "Field Update",
                "description": "Location Updated",
            },
            "fixed_budget": {
                "type": "Field Update",
                "description": "Cash CTC Budget Updated",
            },
        },
    }


class ProspectViewSet(ModelViewSet):
    queryset = (
        Prospect.objects.select_related("created_by", "updated_by", "owner", "lead")
        .filter(is_converted_to_deal=False)
        .order_by("-created_at")
    )
    serializer_class = ProspectSerializer
    permission_classes = [IsAuthenticated]
    filtering = {
        "lead__title": {"operation": "contains", "lookup": "__icontains"},
        "lead__role__region": {"operation": "in", "lookup": "__in"},
        "lead__source": {"operation": "in", "lookup": "__in"},
        "status": {"operation": "in", "lookup": "__in"},
        "owner": {"operation": "in", "lookup": "_id__in"},
        "created_by": {"operation": "in", "lookup": "_id__in"},
        "created_at_from": {"operation": "from_to", "lookup": "__gte"},
        "created_at_to": {"operation": "from_to", "lookup": "__lte"},
    }
    sorting = ["created_at"]
    pagination = True
    user_permissions = {
        "get": ["pipedrive.view_prospect"],
        "post": ["pipedrive.add_prospect"],
        "patch": ["pipedrive.change_prospect"],
    }
    changelog = {
        "model": "Lead",
        "mapping_obj": "lead_id",
        "is_mapping_obj_func": False,
        "update": {
            "status": {
                "type": "Status Update",
                "description": "Prospect State Updated",
            },
            "is_converted_to_deal": {
                "type": "State Update",
                "description": "Prospect Converted to Deal",
            },
            "owner": {
                "field_to_get": "get_full_name",
                "type": "Field Update",
                "description": "Owned by Field Updated",
            },
        },
    }

    def partial_update(self, request, pk):
        check_permisson(self, request)
        prospect = self.get_object()
        serializer = UpdateProspectSerializer(prospect, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        if self.changelog and ("update" in self.changelog):
            changelog(
                self.changelog,
                prospect,
                serializer._validated_data,
                "update",
                request.user.id,
            )
        if prospect.owner_id != serializer._validated_data["owner"].id:
            Notification.objects.create(
                type="Lead Owner Assigned",
                description=f"{request.user.get_full_name()} assigned Ownership for Prospect {prospect.lead.title} to {serializer.validated_data['owner'].get_full_name()}",
                user=serializer.validated_data["owner"],
                model_name="Prospect",
                object_id=prospect.id,
            )
        prospect = serializer.save(updated_by=request.user)
        return custom_success_response(
            ProspectSerializer(prospect).data, status=status.HTTP_200_OK
        )

    @action(detail=True, methods=["patch"])
    def promote(self, request, pk):
        check_permisson(self, request)
        obj = self.get_object()
        if obj.is_converted_to_deal:
            raise ValidationError({"message": ["Prospect already converted to deal"]})
        obj.is_converted_to_deal = True
        obj.updated_by = request.user
        deal = Deal.objects.update_or_create(
            lead=obj.lead,
            prospect=obj,
            defaults={
                "owner": obj.owner,
                "deal_value": request.data.get("deal_value", "0"),
                **set_crated_by_updated_by(request.user),
            },
        )
        if deal:
            changelog(
                self.changelog,
                obj,
                {"is_converted_to_deal": True},
                "update",
                request.user.id,
            )
            obj.save()
            return custom_success_response(self.serializer_class(obj).data)
        else:
            raise ValidationError({"message": ["Technical error"]})

    @action(detail=False, methods=["patch"])
    def bulk_archive(self, request):
        check_permisson(self, request)
        if "prospects" not in request.data:
            raise ValidationError({"prospects": ["List of prospect id(s) is/are required"]})
        if "archive" not in request.data:
            raise ValidationError({"archive": ["This boolean field is required"]})

        prospect = Prospect.objects.filter(id__in=request.data.get("prospects")).update(
            archived=request.data.get("archive")
        )
        if prospect > 0:
            return custom_success_response(
                {
                    "message": [
                        f"{prospect} prospect(s) has been marked archived as {request.data.get('archive')}"
                    ]
                }
            )
        else:
            raise ValidationError({"message": ["Technical error"]})


class DealViewSet(ModelViewSet):
    queryset = Deal.objects.all().order_by("-created_at")
    serializer_class = DealSerializer
    permission_classes = [IsAuthenticated]
    response_serializer = DealSerializer
    filtering = {
        "lead__title": {"operation": "contains", "lookup": "__icontains"},
        "lead__fullfilled_by": {"operation": "in", "lookup": "__in"},
        "lead__source": {"operation": "in", "lookup": "__in"},
        "status": {"operation": "in", "lookup": "__in"},
        "owner": {"operation": "in", "lookup": "_id__in"},
        "created_at_from": {"operation": "from_to", "lookup": "__gte"},
        "created_at_to": {"operation": "from_to", "lookup": "__lte"},
    }
    sorting = ["created_at"]
    pagination = True
    user_permissions = {
        "get": ["pipedrive.view_deal"],
        "post": ["pipedrive.add_deal"],
        "patch": ["pipedrive.change_deal"],
    }
    changelog = {
        "model": "Lead",
        "mapping_obj": "lead_id",
        "is_mapping_obj_func": False,
        "update": {
            "status": {"type": "Status Update", "description": "Deal State Updated"},
            "owner": {
                "field_to_get": "get_full_name",
                "type": "Field Update",
                "description": "Owned by Field Updated",
            },
        },
    }

    def get_serializer_class(self):
        return UpdateDealSerializer if self.request.method in ["PATCH"] else DealSerializer

    @action(detail=False, methods=["patch"])
    def bulk_archive(self, request):
        check_permisson(self, request)
        if "deal" not in request.data:
            raise ValidationError({"deal": ["List of deal id(s) is/are required"]})
        if "archive" not in request.data:
            raise ValidationError({"archive": ["This boolean field is required"]})

        deal = Deal.objects.filter(id__in=request.data.get("deal")).update(
            archived=request.data.get("archive")
        )
        if deal > 0:
            return custom_success_response(
                {
                    "message": [
                        f"{deal} deal(s) has been marked archived as {request.data.get('archive')}"
                    ]
                }
            )
        else:
            raise ValidationError({"message": ["Technical error"]})

    @action(detail=False, methods=["get"])
    def cummulative_summary(self, request):
        deals = Deal.objects.all()
        mapping = {"created_at_from": "created_at__gte", "created_at_to": "created_at__lte"}
        _filters = {}
        for key, value in request.query_params.items():
            _filters[mapping[key] if key in mapping else key] = value
        deals = deals.filter(**_filters).values_list("deal_value")
        cummulative_summary = {"INR": 0, "USD": 0, "EUR": 0, "SGD": 0}
        for deal_value in deals:
            currency, value = deal_value[0].split(" ")
            cummulative_summary.setdefault(currency, 0)
            cummulative_summary[currency] += float(value.replace(",", ""))
        return custom_success_response(cummulative_summary)


class CreateLandingPageLead(CreateAPIView):
    changelog = {
        "model": "Lead",
        "mapping_obj": "id",
        "is_mapping_obj_func": False,
        "create": {
            "is_created": {"type": "Entity Created", "description": "Lead Created"},
        },
    }

    def post(self, request, *args, **kwargs):
        serializer = CreateLeadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        dto = serializer.validated_data
        role_serializer = RoleDetailSerializer(data=dto["role_details"])
        role_serializer.is_valid(raise_exception=True)
        org_id = None
        count = 0
        if Organisation.objects.filter(name=dto["organisation"]["name"]).exists():
            org = Organisation.objects.filter(name=dto["organisation"]["name"]).last()

        else:
            org = Organisation.objects.create(name=dto["organisation"]["name"])
        org_id = org.id
        role = role_serializer.save()
        if "contact_details" in dto["organisation"]:
            for contact in dto["organisation"]["contact_details"]:
                Contact.objects.create(
                    organisation_id=org_id, **contact, **set_crated_by_updated_by(None)
                )
            pass
        count = Lead.objects.filter(
            organisation_id=org_id,
            role__region=dto["role_details"]["region"],
            role__role_type=dto["role_details"]["role_type"],
        ).count()
        lead = Lead.objects.create(
            organisation_id=org_id,
            role=role,
            source=dto["source"],
            title=f'{dto["organisation"]["name"]} - {dto["role_details"]["region"]} - {dto["role_details"]["role_type"]} - {count+1}',
            created_by=None,
            updated_by=None,
        )
        changelog(
            self.changelog,
            lead,
            {"is_created": None},
            "create",
            None,
        )
        slack_send_message(
            "elixir-stage-alerts",
            [
                f"** 🚨 Elixir Alert Triggered **",
                f"*Related to*: Lead Creation",
                f"*For*: <!channel>",
                f"*Entity*: {lead.title}",
                f"*Required Action*: Lead Ownership Assignment",
            ],
        )
        return custom_success_response(
            {"message": "Lead created Successfully"}, status=status.HTTP_201_CREATED
        )


class ServiceProposalViewSet(ModelViewSet):
    queryset = ServiceProposal.objects.all()
    permission_classes = [IsAuthenticated]
    serializer_class = ServiceProposalSerializer
    http_method_names = ["post", "get"]

    def list(self, request, *args, **kwargs):
        prospect = request.query_params.get("prospect", None)
        if prospect:
            return custom_success_response(
                self.get_serializer(self.queryset.filter(prospect=prospect), many=True).data
            )
        else:
            raise ValidationError({"prospect": ["This field is required"]})

    def perform_create(self, serializer, **kwargs):
        self._instance = serializer.save(uploaded_by=self.request.user)


class ServiceContractViewSet(ModelViewSet):
    queryset = ServiceContract.objects.all().select_related("docusign")
    permission_classes = [IsAuthenticated]
    serializer_class = ServiceContractSerializer
    http_method_names = ["post", "get"]

    def list(self, request, *args, **kwargs):
        deal = request.query_params.get("deal", None)
        if deal:
            return custom_success_response(
                self.get_serializer(self.queryset.filter(deal=deal), many=True).data
            )
        else:
            raise ValidationError({"deal": ["This field is required"]})

    def perform_create(self, serializer, **kwargs):
        if serializer.validated_data["document_type"] == "Signed Contract":
            serializer.validated_data["status"] = "Completed"
        self._instance = serializer.save(uploaded_by=self.request.user)

    @action(detail=False, methods=["post"])
    def export_zoho(self, request):
        pass

    @action(detail=True, methods=["post"])
    def docu_esign(self, request, pk):
        """
        1-Api to send envelop to docusign
        2-update the linked docusign field in service contract obj
        3- update status and event_date field
        """
        obj = self.get_object()
        docusign_envelop = create_envelop(obj)
        if "errorCode" not in docusign_envelop:
            scdd = ServiceContractDocuSignDetail.objects.create(
                status=docusign_envelop["status"],
                file_url=docusign_envelop["uri"],
                envelop_id=docusign_envelop["envelopeId"],
                response=docusign_envelop,
            )
            obj.docusign = scdd
            obj.event_date = docusign_envelop["statusDateTime"]
            obj.save()
        else:
            raise ValidationError(detail={"errorCode": [docusign_envelop["errorCode"]]})

        return custom_success_response({"messsage": ["E-sign successful."]})

    @action(detail=True, methods=["get"])
    def docu_view_document(self, request, pk):
        obj = self.get_object()
        if obj.docusign and obj.document_type == "Draft Contract":
            docusign_envelop = view_document(obj)
            return HttpResponse(docusign_envelop, content_type="application/pdf")
        elif obj.document_type == "Signed Contract":
            return HttpResponse(obj.file, content_type="application/pdf")
        else:
            raise ValidationError({"document": "No document has been esigned to Docusign"})


class RDCapsuleViewSet(ModelViewSet):
    queryset = RDCapsule.objects.all()
    permission_classes = [IsAuthenticated]
    serializer_class = RDCapsuleSerializer
    http_method_names = ["post", "get"]

    def list(self, request, *args, **kwargs):
        deal = request.query_params.get("deal", None)
        if deal:
            return custom_success_response(
                self.get_serializer(self.queryset.filter(deal=deal), many=True).data
            )
        else:
            raise ValidationError({"deal": ["This field is required"]})

    def perform_create(self, serializer, **kwargs):
        self._instance = serializer.save(uploaded_by=self.request.user)
