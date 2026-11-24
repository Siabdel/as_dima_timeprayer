"""
Tests de l'app events :
- services : fêtes d'une année grégorienne, prochaines fêtes, année hégirienne
- endpoint /api/v1/events/ (public, filtre ?year=, validation)
- endpoint /api/v1/events/upcoming/ (public)
- endpoint /api/v1/events/hijri-year/ (public)
"""
from datetime import date

import pytest
from hijridate import Hijri

from apps.events import services

pytestmark = pytest.mark.django_db


class TestEventServices:
    def test_year_events_sorted_and_typed(self):
        events = services.get_year_events(2026)
        assert len(events) >= 9  # 9 fêtes marocaines + les islamiques
        dates = [e["date"] for e in events]
        assert dates == sorted(dates)
        types = {e["type"] for e in events}
        assert types == {"islamic", "national"}

    def test_national_events_fixed_dates(self):
        events = services.get_year_events(2026)
        throne = next(e for e in events if e["id"] == "throne-day")
        assert throne["date"] == "2026-07-30"
        assert throne["type"] == "national"
        green_march = next(e for e in events if e["id"] == "green-march")
        assert green_march["date"] == "2026-11-06"

    def test_ramadan_start_is_islamic_with_hijri(self):
        events = services.get_year_events(2026)
        ramadan = next(e for e in events if e["id"] == "ramadan-start")
        assert ramadan["type"] == "islamic"
        assert ramadan["hijri_date"]["month"] == 9
        assert ramadan["hijri_date"]["day"] == 1
        # La date grégorienne découle réellement de la conversion hégirienne.
        hijri = ramadan["hijri_date"]
        greg = Hijri(hijri["year"], hijri["month"], hijri["day"]).to_gregorian()
        assert greg.isoformat() == ramadan["date"]

    def test_upcoming_events_have_days_until(self):
        events = services.get_upcoming_events(from_date=date(2026, 11, 18), limit=5)
        assert len(events) == 5
        assert all(e["days_until"] >= 0 for e in events)
        # Trié par proximité.
        delays = [e["days_until"] for e in events]
        assert delays == sorted(delays)

    def test_hijri_year_events(self):
        events = services.get_hijri_year_events(1447)
        assert len(events) == len(services.ISLAMIC_EVENTS)
        months = [e["hijri_date"]["month"] for e in events]
        assert months == sorted(months)


class TestEventsEndpoint:
    def test_public_default_year(self, api_client):
        resp = api_client.get("/api/v1/events/")
        assert resp.status_code == 200
        assert resp.data["year"] == date.today().year
        assert resp.data["count"] == len(resp.data["events"])

    def test_year_filter(self, api_client):
        resp = api_client.get("/api/v1/events/", {"year": 2027})
        assert resp.status_code == 200
        assert resp.data["year"] == 2027
        assert all(e["date"].startswith("2027") for e in resp.data["events"])

    def test_year_out_of_range(self, api_client):
        resp = api_client.get("/api/v1/events/", {"year": 1800})
        assert resp.status_code == 400

    def test_upcoming_endpoint(self, api_client):
        resp = api_client.get("/api/v1/events/upcoming/")
        assert resp.status_code == 200
        assert len(resp.data["events"]) <= 12
        assert all("days_until" in e for e in resp.data["events"])

    def test_hijri_year_endpoint(self, api_client):
        resp = api_client.get("/api/v1/events/hijri-year/", {"year": 1447})
        assert resp.status_code == 200
        assert resp.data["hijri_year"] == 1447
        assert len(resp.data["events"]) == 9

    def test_hijri_year_default_current(self, api_client):
        resp = api_client.get("/api/v1/events/hijri-year/")
        assert resp.status_code == 200
        assert 1400 <= resp.data["hijri_year"] <= 1500
