from typing import Any

from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated

from apps.client.models import Contact, Organisation
from apps.client.serializer import ContactSerializer, OrganisationSerializer
from elixir.utils import custom_success_response, set_crated_by_updated_by
from elixir.viewsets import ModelViewSet


# Create your views here.
class OrganisationViewSet(ModelViewSet):
    queryset = Organisation.objects.all()
    serializer_class = OrganisationSerializer
    permission_classes = [IsAuthenticated]

    def __init__(self, **kwargs: Any) -> None:
        self.user_permissions["get"] = ["client.access_organisation", "client.view_organisation"]
        self.user_permissions["post"] = ["client.access_organisation", "client.add_organisation"]
        self.user_permissions["patch"] = [
            "client.access_organisation",
            "client.change_organisation",
        ]

    def create(self, request, *args, **kwargs):
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


class ContactViewSet(ModelViewSet):
    queryset = Contact.objects.all()
    serializer_class = ContactSerializer
    permission_classes = [IsAuthenticated]

    def __init__(self, **kwargs: Any) -> None:
        self.user_permissions["get"] = ["client.access_organisation", "client.view_organisation"]
        self.user_permissions["post"] = ["client.add_organisation"]
        self.user_permissions["patch"] = ["client.change_organisation"]
