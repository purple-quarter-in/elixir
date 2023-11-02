from datetime import date, datetime
from urllib import request

from django.shortcuts import render
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.generics import CreateAPIView
from rest_framework.permissions import IsAuthenticated
from yaml import serialize

from apps.client.models import Contact, Organisation
from apps.pipedrive.models import Lead, Prospect, RDCapsule, RoleDetail, ServiceContract
from apps.pipedrive.serializer import (
    CreateLeadSerializer,
    LeadSerializer,
    ProspectSerializer,
    RDCapsuleSerializer,
    RoleDetailSerializer,
    ServiceContractSerializer,
    UpdateLeadSerializer,
    UpdateProspectSerializer,
)
from elixir.changelog import changelog
from elixir.utils import custom_success_response, set_crated_by_updated_by
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
    queryset = Lead.objects.filter(is_converted_to_prospect=False).order_by("-created_at")
    serializer_class = LeadSerializer
    permission_classes = [IsAuthenticated]
    user_permissions = {
        "get": ["pipedrive.view_lead"],
        "post": ["pipedrive.create_lead"],
        "patch": ["pipedrive.update_lead"],
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
                "description": "service_fee updated",
            },
            "owner": {
                "field_to_get": "get_full_name",
                "type": "Field Update",
                "description": "Field Updated",
            },
            "closed_by": {
                "field_to_get": "get_full_name",
                "type": "Field Update",
                "description": "Field Updated",
            },
            "fullfilled_by": {
                "field_to_get": "get_full_name",
                "type": "Field Update",
                "description": "Field Updated",
            },
        },
    }

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
                    Contact.objects.create(
                        organisation_id=org_id, **contact, **set_crated_by_updated_by(request.user)
                    )
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
                    Contact.objects.create(
                        organisation_id=org_id, **contact, **set_crated_by_updated_by(request.user)
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
        obj = self.get_object()
        if obj.is_converted_to_prospect:
            raise ValidationError({"message": ["Lead already converted to prospect"]})
        obj.is_converted_to_prospect = True
        obj.updated_by = request.user
        prospect = Prospect.objects.update_or_create(
            lead=obj, defaults={"owner": obj.owner, **set_crated_by_updated_by(request.user)}
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
    queryset = Prospect.objects.all().order_by("-created_at")
    serializer_class = ProspectSerializer
    permission_classes = [IsAuthenticated]
    user_permissions = {
        "get": ["pipedrive.view_prospect"],
        "post": ["pipedrive.create_prospect"],
        "patch": ["pipedrive.update_prospect"],
    }
    changelog = {
        "model": "Lead",
        "mapping_obj": "lead_id",
        "is_mapping_obj_func": False,
        "update": {
            "status": {"type": "Status Update", "description": "Prospect State Updated"},
            "is_converted_to_deal": {
                "type": "State Update",
                "description": "Prospect Converted to Deal",
            },
        },
    }

    def partial_update(self, request, pk):
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
        prospect = serializer.save(updated_by=request.user)
        return custom_success_response(
            ProspectSerializer(prospect).data, status=status.HTTP_200_OK
        )

    @action(detail=False, methods=["patch"])
    def bulk_archive(self, request):
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

    # @action(detail=False, methods=["post"], permission_classes=[IsAuthenticated])
    # def contract(self, request):
    #     # obj = self.get_object(pk=request.data.get("prospect"))


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
        return custom_success_response(
            {"message": "Lead created Successfully"}, status=status.HTTP_201_CREATED
        )


class ServiceContractViewSet(ModelViewSet):
    queryset = ServiceContract.objects.all()
    permission_classes = [IsAuthenticated]
    serializer_class = ServiceContractSerializer
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


class RDCapsuleViewSet(ModelViewSet):
    queryset = RDCapsule.objects.all()
    permission_classes = [IsAuthenticated]
    serializer_class = RDCapsuleSerializer
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
