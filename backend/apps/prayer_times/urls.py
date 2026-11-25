"""URLs de l'app prayer_times (montées sous /api/v1/prayer-times/)."""
from django.urls import path

from .views import PrayerTimesTodayView, PrayerTimesView, RamadanCalendarView

urlpatterns = [
    path("", PrayerTimesView.as_view(), name="prayer-times"),
    path("ramadan/", RamadanCalendarView.as_view(), name="prayer-times-ramadan"),
    path("today/", PrayerTimesTodayView.as_view(), name="prayer-times-today"),
]
