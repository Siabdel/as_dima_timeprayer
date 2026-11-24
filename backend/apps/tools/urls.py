"""URLs de l'app tools (montées sous /api/v1/)."""
from django.urls import path

from .views import HijriView, QiblaView

urlpatterns = [
    path("qibla/", QiblaView.as_view(), name="qibla"),
    path("hijri/", HijriView.as_view(), name="hijri"),
]
