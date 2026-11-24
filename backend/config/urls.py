"""URLs racine du projet : administration, API versionnée et healthcheck."""
from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path

from config.api_router import api_urlpatterns


def health(request):
    """Endpoint de santé pour les orchestrateurs (compose, k8s…)."""
    return JsonResponse({"status": "ok"})


urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/", include(api_urlpatterns)),
    path("health/", health),
]
