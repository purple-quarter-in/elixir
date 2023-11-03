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
from apps.pipedrive.models import Lead
from elixir.utils import (
    check_permisson,
    custom_success_response,
    set_crated_by_updated_by,
)
from elixir.viewsets import ModelViewSet


# Create your views here.
class OrganisationViewSet(ModelViewSet):
    queryset = Organisation.objects.all().order_by("-created_at")
    serializer_class = OrganisationSerializer
    permission_classes = [IsAuthenticated]
    user_permissions = {}

    def __init__(self, **kwargs: Any) -> None:
        self.user_permissions["get"] = ["client.access_organisation", "client.view_organisation"]
        self.user_permissions["post"] = ["client.access_organisation", "client.add_organisation"]
        self.user_permissions["patch"] = [
            "client.access_organisation",
            "client.change_organisation",
        ]

    def create(self, request, *args, **kwargs):
        check_permisson(self, request)
        serializer = OrganisationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        if Organisation.objects.filter(name=serializer.validated_data["name"]).exists():
            raise ValidationError(
                {
                    "already_exists": [
                        f'Organisation with name {serializer.validated_data["name"]} already exists'
                    ]
                }
            )
        org = serializer.save(**set_crated_by_updated_by(request.user))
        if "contact_details" in request.data:
            for contact in request.data.get("contact_details"):
                Contact.objects.create(organisation=org, **contact)
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
        obj.name = request.data.get("name")
        obj.save()
        return custom_success_response({"message": "Organisatiomn name updates successfully"})


class ContactViewSet(ModelViewSet):
    queryset = Contact.objects.all().order_by("-created_at")
    serializer_class = ContactSerializer
    permission_classes = [IsAuthenticated]
    response_serializer = ContactSerializer
    user_permissions = {}

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

    def create(self, request, *args, **kwargs):
        check_permisson(self, request)
        if request.user.has_perms(self.user_permissions["post"]):
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
                    name=request.data.get("organisation_name")
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
                    **request.data, **set_crated_by_updated_by(request.user), organisation=org
                )
                return custom_success_response(self.get_serializer(contact).data)
        else:
            raise PermissionDenied()

    def perform_update(self, serializer):
        self._instance = serializer.save(**(set_crated_by_updated_by(self.request.user)))

    @action(detail=False, methods=["get"])
    def is_duplicate(self, request):
        check_permisson(self, request)
        is_duplicate = False
        phone = request.query_params.get("phone", None)
        email = request.query_params.get("email", None)
        errors = {}
        if phone:
            std, number = phone.split(" ")
            is_phone = Contact.objects.filter(phone=number, std_code=std).exists()
            is_duplicate = is_duplicate or is_phone
            errors["phone"] = is_duplicate
        if email:
            is_email = Contact.objects.filter(email=email).exists()
            is_duplicate = is_duplicate or is_email
            errors["email"] = is_duplicate
        errors["is_duplicate"] = is_duplicate
        return custom_success_response(errors)
