"""
URL configuration for elixir project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework.routers import DefaultRouter
from rest_framework.schemas import get_schema_view

from apps.django_rest_passwordreset.urls import urlpatterns as reset_urlpatterns
from apps.user.urls import urlpatterns as user_urlpatterns

from . import settings

urlpatterns = [
    path("admin/", admin.site.urls),
]
from apps.client.urls import router as client_router
from apps.pipedrive.urls import router as pipedrive_router
from apps.rbac.urls import router as rbac_router
from apps.user.urls import router as user_router

router = DefaultRouter()
# router.registry.extend(campaign_router.registry)
router.registry.extend(rbac_router.registry)
router.registry.extend(pipedrive_router.registry)
router.registry.extend(client_router.registry)
router.registry.extend(user_router.registry)
urlpatterns = [
    path("jet/", include("jet.urls", "jet")),
    path("jet/dashboard/", include("jet.dashboard.urls", "jet-dashboard")),
    path("admin/", admin.site.urls),
    path("v1/api/", include(user_urlpatterns)),
    path("v1/api/password_reset/", include(reset_urlpatterns)),
    path("v1/api/", include(router.urls)),
    path(
        "openapi",
        get_schema_view(
            title="Your Project",
            description="API for all things …",
            version="1.0.0",
            urlconf="elixir.urls",
        ),
        name="openapi-schema",
    ),
    path("schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "docs/",
        SpectacularSwaggerView.as_view(template_name="swagger-ui.html", url_name="schema"),
        name="swagger-ui",
    ),
]
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
