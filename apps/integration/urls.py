from django.urls import path
from rest_framework.routers import DefaultRouter

from apps.integration.docusign import listen_event, oauth, refresh_access_token
from apps.integration.views.integration_view import IntegrationViewSet

router = DefaultRouter()
router.register("integrations", IntegrationViewSet)
url_pattern = [
    path("hook_docusign/oauth", oauth),
    path("docusign_refresh_token", refresh_access_token),
    path("hook/docusign", listen_event),
]
