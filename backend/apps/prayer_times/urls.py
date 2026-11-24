"""URLs de l'app prayer_times (montées sous /api/v1/prayer-times/)."""
from django.urls import path

from .views import PrayerTimesTodayView, PrayerTimesView

urlpatterns = [
    path("", PrayerTimesView.as_view(), name="prayer-times"),
    path("today/", PrayerTimesTodayView.as_view(), name="prayer-times-today"),
]
