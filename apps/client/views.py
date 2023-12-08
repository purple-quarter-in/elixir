from typing import Any

from rest_framework import status
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated

from apps.client.models import Contact, Organisation
from apps.client.serializer import (
    ContactSerializer,
    CreateContactSerializer,
    OrganisationSerializer,
)
from apps.pipedrive.models import Deal, Lead, Prospect
from apps.pipedrive.serializer import DealSerializer, LeadSerializer, ProspectSerializer
from elixir.changelog import changelog
from elixir.utils import (
    check_permisson,
    custom_success_response,
    set_crated_by_updated_by,
)
from elixir.viewsets import ModelViewSet


# Create your views here.
class OrganisationViewSet(ModelViewSet):
    queryset = (
        Organisation.objects.select_related("created_by", "updated_by")
        .prefetch_related("contact_organisation", "lead_organisation")
        .order_by("-created_at")
    )
    serializer_class = OrganisationSerializer
    permission_classes = [IsAuthenticated]
    user_permissions = {}
    filtering = {
        "name": {"operation": "contains", "lookup": "__icontains"},
        "industry": {"operation": "in", "lookup": "__in"},
        "segment": {"operation": "in", "lookup": "__in"},
        "last_funding_stage": {"operation": "in", "lookup": "__in"},
        "created_by": {"operation": "in", "lookup": "_id__in"},
        "created_at_from": {"operation": "from_to", "lookup": "__gte"},
        "created_at_to": {"operation": "from_to", "lookup": "__lte"},
    }
    sorting = ["created_at"]
    pagination = True
    changelog = {
        "model": "Organisation",
        "mapping_obj": "id",
        "is_mapping_obj_func": False,
        "create": {
            "is_created": {"type": "Entity Created", "description": "Account Created"},
        },
        "update": {
            "industry": {
                "type": "Field Update",
                "description": "Industry Updated",
            },
            "name": {
                "type": "Field Update",
                "description": "Name Updated",
            },
            "govt_id": {
                "type": "Field Update",
                "description": " GSTIN/VAT/GST Updated",
            },
            "last_funding_stage": {
                "type": "Field Update",
                "description": " Last Funding Round Updated",
            },
        },
    }
    # X assigned Ownership for Lead Zomato-IND-HOE-1 to Y

    def __init__(self, **kwargs: Any) -> None:
        self.user_permissions["get"] = [
            "client.access_organisation",
            "client.view_organisation",
        ]
        self.user_permissions["post"] = [
            "client.access_organisation",
            "client.add_organisation",
        ]
        self.user_permissions["patch"] = [
            "client.access_organisation",
            "client.change_organisation",
        ]

    def create(self, request, *args, **kwargs):
        check_permisson(self, request)
        serializer = OrganisationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        if Organisation.objects.filter(name__iexact=serializer.validated_data["name"]).exists():
            raise ValidationError(
                {
                    "already_exists": [
                        f'Organisation with name {serializer.validated_data["name"]} already exists'
                    ]
                }
            )
        org = serializer.save(**set_crated_by_updated_by(request.user))
        changelog(
            self.changelog,
            org,
            {"is_created": request.user},
            "create",
            request.user.id,
        )
        if "contact_details" in request.data:
            for contact in request.data.get("contact_details"):
                Contact.objects.create(
                    organisation=org,
                    **contact,
                    **set_crated_by_updated_by(request.user),
                )
        return custom_success_response(
            self.serializer_class(org).data, status=status.HTTP_201_CREATED
        )

    @action(detail=True, methods=["patch"])
    def org_name(self, request, pk):
        check_permisson(self, request)
        obj = self.get_object()
        if not request.data.get("name") or request.data.get("name") == "":
            raise ValidationError({"name": ["This field is required and cannot be blank."]})
        if obj.name == request.data.get("name"):
            raise ValidationError({"message": ["No change in Name detected"]})
        leads = Lead.objects.filter(organisation=obj)
        for lead in leads:
            name_split = (lead.title).split("-")
            name_split[0] = request.data.get("name")
            lead.title = " - ".join(name_split)
            lead.save()
        changelog(
            self.changelog,
            obj,
            {"name": request.data.get("name")},
            "update",
            request.user.id,
        )
        obj.name = request.data.get("name")
        obj.save()
        return custom_success_response({"message": "Organisatiomn name updates successfully"})

    @action(detail=True, methods=["get"])
    def related_entities(self, request, pk):
        check_permisson(self, request)
        # org = Organisation.objects.filter(id=pk).prefetch_related("lead_organisation")
        leads = Lead.objects.filter(organisation_id=pk, is_converted_to_prospect=False)
        prospects = Prospect.objects.filter(
            lead__organisation_id=pk, is_converted_to_deal=False
        ).select_related("lead")
        deals = Deal.objects.filter(lead__organisation_id=pk).select_related("lead")
        res = {
            "leads": LeadSerializer(leads, many=True).data,
            "prospects": ProspectSerializer(prospects, many=True).data,
            "deal": DealSerializer(deals, many=True).data,
        }

        # temp_dict={
        #     "title":lead.title,
        #     "source":lead.source,
        #     "created_by":lead.created_by.get_dict_name_id() if lead.created_by else None,
        #     "owned_by":lead.owned_by.get_dict_name_id() if lead.owned_by else None,
        #     "status":lead.status,
        #     "created_at":lead.created_at,
        # }
        return custom_success_response(res)


class ContactViewSet(ModelViewSet):
    queryset = Contact.objects.select_related("created_by", "updated_by").order_by("-created_at")
    serializer_class = ContactSerializer
    permission_classes = [IsAuthenticated]
    response_serializer = ContactSerializer
    user_permissions = {}
    filtering = {
        "name": {"operation": "contains", "lookup": "__icontains"},
        "organisation__name": {"operation": "in", "lookup": "__in"},
        "designation": {"operation": "in", "lookup": "__in"},
        "type": {"operation": "in", "lookup": "__in"},
        "created_by": {"operation": "in", "lookup": "_id__in"},
        "created_at_from": {"operation": "from_to", "lookup": "__gte"},
        "created_at_to": {"operation": "from_to", "lookup": "__lte"},
    }
    sorting = ["created_at"]
    pagination = True

    def __init__(self, **kwargs: Any) -> None:
        self.user_permissions["get"] = ["client.view_contact"]
        self.user_permissions["post"] = ["client.add_contact"]
        self.user_permissions["patch"] = ["client.change_contact"]

    def get_serializer_class(self):
        return (
            CreateContactSerializer
            if self.request.method in ["POST", "PATCH"]
            else ContactSerializer
        )

    def check_duplicate(self, std, number, email):
        errors = {}
        duplicate = False
        if number:
            is_phone = Contact.objects.filter(phone=number, std_code=std).exists()
            duplicate = is_phone or duplicate
            errors["phone"] = is_phone
        if email:
            is_email = Contact.objects.filter(email=email).exists()
            duplicate = duplicate or is_email
            errors["email"] = is_email
        errors["is_duplicate"] = duplicate
        return errors

    def create(self, request, *args, **kwargs):
        check_permisson(self, request)
        errors = self.check_duplicate(
            request.data.get("std_code", None),
            request.data.get("phone", None),
            request.data.get("email", None),
        )
        if errors and errors["is_duplicate"]:
            raise ValidationError(errors)
        if "organisation" in request.data:
            serializer = CreateContactSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)

            serializer.save(**set_crated_by_updated_by(request.user))
            return custom_success_response(
                serializer.data,
                status=status.HTTP_201_CREATED,
            )
        elif "organisation_name" in request.data:
            if Organisation.objects.filter(
                name__iexact=request.data.get("organisation_name")
            ).exists():
                raise ValidationError(
                    {
                        "already_exists": [
                            f'Organisation with name {request.data.get("organisation_name")} already exists'
                        ]
                    }
                )
            org = Organisation.objects.create(
                name=request.data.get("organisation_name"),
                **set_crated_by_updated_by(request.user),
            )
            request.data.pop("organisation_name")
            contact = Contact.objects.create(
                **request.data,
                **set_crated_by_updated_by(request.user),
                organisation=org,
            )
            return custom_success_response(self.get_serializer(contact).data)

    def perform_update(self, serializer):
        errors = self.check_duplicate(
            serializer.validated_data.get("std_code", None),
            serializer.validated_data.get("phone", None),
            serializer.validated_data.get("email", None),
        )
        if errors and errors["is_duplicate"]:
            raise ValidationError(errors)
        self._instance = serializer.save(**(set_crated_by_updated_by(self.request.user)))

    @action(detail=False, methods=["get"])
    def is_duplicate(self, request):
        check_permisson(self, request)
        number = request.query_params.get("phone", None)
        email = request.query_params.get("email", None)
        std = None
        if number:
            std, number = number.split("-")
            std = "+" + std[1:]
        errors = self.check_duplicate(std, number, email)
        return custom_success_response(errors)
