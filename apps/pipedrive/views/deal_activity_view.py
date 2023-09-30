from datetime import datetime

from django import views
from django.shortcuts import render
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated

from apps.client.models import Contact, Organisation
from apps.pipedrive.models import Activity, Lead, Note, Prospect, RoleDetail
from apps.pipedrive.models import changelog as Changelog
from apps.pipedrive.serializer import (
    ActivitySerializer,
    ChangelogSerializer,
    CreateLeadSerializer,
    HistoryNoteSerializer,
    LeadSerializer,
    NoteSerializer,
    ProspectSerializer,
    RoleDetailSerializer,
    UpdateLeadSerializer,
)
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
class ActivityViewSet(ModelViewSet):
    queryset = Activity.objects.all()
    serializer_class = ActivitySerializer
    permission_classes = [IsAuthenticated]
    user_permissions = {
        "get": ["pipedrive.view_lead"],
        "post": ["pipedrive.create_lead"],
        "patch": ["pipedrive.update_lead"],
    }

    @action(detail=False, methods=["get"])
    def to_do(self, request):
        if "lead" not in request.query_params:
            raise ValidationError({"lead": ["Lead id not provided."]})
        return custom_success_response(
            self.serializer_class(
                Activity.objects.filter(
                    lead=request.query_params.get("lead"), closed_at=None
                ).order_by("-created_at"),
                many=True,
            ).data
        )

    @action(detail=True, methods=["patch"])
    def update_status(self, request, pk):
        if "status" not in request.data:
            raise ValidationError({"status": ["Status id not provided."]})
        obj = self.get_object()
        obj.status = request.data.get("status")
        obj.closed_at = datetime.now()
        obj.save()
        return custom_success_response({"message": "Status updated successfully"})


class NoteViewSet(ModelViewSet):
    queryset = Note.objects.all()
    serializer_class = NoteSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ["get", "post"]


class History(ListAPIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        if "lead" not in request.query_params:
            raise ValidationError({"lead": ["Lead id not provided."]})
        lead = request.query_params.get("lead")
        activity = Activity.objects.filter(lead_id=lead).order_by("-created_at")
        activity_ids = []
        activity_data = []
        for act in activity:
            activity_ids.append(act.id)
            if act.closed_at:
                activity_data.append(ActivitySerializer(act).data)
        notes = HistoryNoteSerializer(
            Note.objects.filter(activity_id__in=activity_ids).order_by("-created_at"),
            many=True,
        ).data
        # activity_data = ActivitySerializer(
        #     activity,
        #     many=True,
        # ).data
        changelog = ChangelogSerializer(
            Changelog.objects.filter(model_name="Lead", obj_id=lead).order_by("-created_at"),
            many=True,
        ).data
        return custom_success_response(
            {"notes": notes, "activity": activity_data, "changelog": changelog}
        )
