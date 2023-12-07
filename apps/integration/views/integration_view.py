from typing import Any

from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated

from apps.integration.models import Integration
from apps.integration.serializer import IntegrationSerializer
from elixir.utils import custom_success_response
from elixir.viewsets import ModelViewSet


class IntegrationViewSet(ModelViewSet):
    queryset = Integration.objects.all().filter(archived=False)
    permission_classes = [IsAuthenticated]
    serializer_class = IntegrationSerializer
    user_permissions = {}
    http_method_names = ["post", "get", "patch"]

    def __init__(self, **kwargs: Any) -> None:
        self.user_permissions["get"] = ["user.view_user"]
        self.user_permissions["post"] = ["user.add_user"]
        self.user_permissions["patch"] = ["user.change_user"]
        self.user_permissions["delete"] = ["user.delete_user"]

    def perform_create(self, serializer, **kwargs):
        self._instance = serializer.save(uploaded_by=self.request.user)
