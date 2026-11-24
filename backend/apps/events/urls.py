"""URLs de l'app events (montées sous /api/v1/events/)."""
from django.urls import path

from .views import EventsView, HijriYearEventsView, UpcomingEventsView

urlpatterns = [
    path("", EventsView.as_view(), name="events"),
    path("upcoming/", UpcomingEventsView.as_view(), name="events-upcoming"),
    path("hijri-year/", HijriYearEventsView.as_view(), name="events-hijri-year"),
]
