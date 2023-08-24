from django.shortcuts import render
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated

from apps.client.models import Contact, Organisation
from apps.pipedrive.models import Lead, RoleDetail
from apps.pipedrive.serializer import (
    CreateLeadSerializer,
    LeadSerializer,
    RoleDetailSerializer,
    UpdateLeadSerializer,
)
from elixir.utils import custom_success_response
from elixir.viewsets import ModelViewSet


def say_hello(request):
    return render(request=request, template_name="email/contact.html")


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
    queryset = Lead.objects.all()
    serializer_class = LeadSerializer
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        # if request.user.has_perms(['pipedrive.access_lead','pipedrive.create_lead','client.access_organisation','client.add_organisation'])
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
                    Contact.objects.create(organisation_id=org_id, **contact)
        elif "id" not in dto["organisation"] and "name" in dto["organisation"]:
            # case of create
            if Organisation.objects.filter(name=dto["organisation"]).exists():
                raise ValidationError(
                    {
                        "already_exists": [
                            f'Organisation with name {dto["organisation"]["name"]} already exists'
                        ]
                    }
                )
            org = Organisation.objects.create(
                name=dto["organisation"]["name"], created_by=request.user, updated_by=request.user
            )
            org_id = org.id
            if "contact_details" in dto["organisation"]:
                for contact in dto["organisation"]["contact_details"]:
                    Contact.objects.create(organisation_id=org_id, **contact)
            pass
        role = role_serializer.save()
        Lead.objects.create(
            organisation_id=org_id,
            role=role,
            source=dto["source"],
            created_by=request.user,
            updated_by=request.user,
            owner=request.user,
        )
        return custom_success_response(
            {"message": "Lead created Successfully"}, status=status.HTTP_201_CREATED
        )

    def partial_update(self, request, pk):
        lead = self.get_object()
        serializer = UpdateLeadSerializer(lead, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save(updated_by=request.user)
        return custom_success_response(serializer.data, status=status.HTTP_200_OK)


class RoleDetailViewSet(ModelViewSet):
    queryset = RoleDetail.objects.all()
    serializer_class = RoleDetailSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ["get", "patch"]
