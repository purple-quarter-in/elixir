from datetime import datetime, time, timedelta

from django.shortcuts import render
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated

from apps.notification.models import Notification
from apps.notification.views import schedule_create_notification
from apps.pipedrive.models import Activity, Note
from apps.pipedrive.models import changelog as Changelog
from apps.pipedrive.serializer import (
    ActivitySerializer,
    ChangelogSerializer,
    DropDownActivitySerializer,
    HistoryNoteSerializer,
    NoteSerializer,
)
from elixir.utils import custom_success_response
from elixir.viewsets import ModelViewSet
from elixir.wsgi import Apschedular


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
    # permission_classes = [IsAuthenticated]
    user_permissions = {
        "get": ["pipedrive.view_lead"],
        "post": ["pipedrive.create_lead"],
        "patch": ["pipedrive.update_lead"],
    }

    def perform_create(self, serializer, **kwargs):
        super().perform_create(serializer, **kwargs)
        Notification.objects.create(
            type="Activity Assigned",
            description=" X Activity has been created and assugned to you",
            user=self._instance.assigned_to,
            model_name="Activity",
            object_id=self._instance.id,
        )
        if self._instance.reminder > 0:
            Apschedular.scheduler.add_job(
                schedule_create_notification,
                trigger="date",
                run_date=self._instance.due_date - timedelta(minutes=self._instance.reminder),
                id=f"schedule_create_notification-activity_reminder-{self._instance.id}",  # The `id` assigned to each job MUST be unique
                max_instances=1,
                kwargs={
                    "instance": self._instance,
                    "type": "Activity Reminder",
                    "description": " X Activity is due in x mins",
                    "user": self._instance.assigned_to,
                    "model_name": "Activity",
                },
                replace_existing=True,
            )
        return

    def perform_update(self, serializer):
        if "due_date" in serializer.initial_data:
            self._instance = serializer.save(rescheduled=serializer.instance.rescheduled + 1)
        else:
            self._instance = serializer.save()

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

    @action(detail=False, methods=["get"])
    def activity_wo_notes(self, request):
        if "lead" not in request.query_params:
            raise ValidationError({"lead": ["Lead id not provided."]})
        sql = f"SELECT * FROM `pipedrive_activity` as pa LEFT OUTER JOIN `pipedrive_note` pn ON pn.activity_id=pa.id WHERE pn.activity_id IS NULL And pa.lead_id={request.query_params.get('lead')};"
        activity = Activity.objects.raw(sql)
        return custom_success_response(ActivitySerializer(activity, many=True).data)


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
        activity = Activity.objects.filter(lead_id=lead).order_by("due_date")
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