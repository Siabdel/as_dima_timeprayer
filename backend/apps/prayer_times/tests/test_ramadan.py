"""Tests du calendrier de Ramadan : normalisation, dates clés, vue, cache."""
import pytest
import responses
from django.core.cache import cache
from django.urls import reverse

from apps.prayer_times.services import aladhan, ramadan

pytestmark = pytest.mark.django_db


def _entry(day, greg):
    return {
        "timings": {"Imsak": "06:10 (CET)", "Fajr": "06:20 (CET)", "Sunrise": "07:40 (CET)",
                    "Dhuhr": "13:00 (CET)", "Asr": "15:30 (CET)", "Maghrib": "18:00 (CET)",
                    "Isha": "19:10 (CET)"},
        "date": {"gregorian": {"date": greg}, "hijri": {"day": str(day)}},
        "meta": {"timezone": "Europe/Paris"},
    }


def _month(n=29):
    from datetime import date, timedelta
    start = date(2027, 2, 8)
    return {"status": "OK", "data": [
        _entry(i + 1, (start + timedelta(days=i)).strftime("%d-%m-%Y")) for i in range(n)]}


@pytest.fixture(autouse=True)
def _clean():
    cache.clear()
    yield
    cache.clear()


class TestKeyDates:
    def test_laylat_al_qadr_is_evening_of_26(self):
        days = aladhan.fetch_ramadan_calendar.__globals__["_normalize_ramadan_day"]
        parsed = [days(e) for e in _month()["data"]]
        keys = {k["id"]: k for k in ramadan.build_key_dates(parsed)}
        assert keys["first-day"]["date"] == "2027-02-08"
        assert keys["laylat-al-qadr"]["date"] == "2027-03-05"  # soir du 26e jour
        assert keys["laylat-al-qadr"]["hijri_day"] == 27
        assert keys["eid-al-fitr"]["date"] == "2027-03-09"  # lendemain du 29e jour
        assert [k["date"] for k in ramadan.build_key_dates(parsed)] == sorted(
            k["date"] for k in ramadan.build_key_dates(parsed))

    def test_30_day_month_moves_eid(self):
        parsed = [aladhan._normalize_ramadan_day(e) for e in _month(30)["data"]]
        keys = {k["id"]: k for k in ramadan.build_key_dates(parsed)}
        assert keys["eid-al-fitr"]["date"] == "2027-03-10"


class TestView:
    URL = "prayer-times-ramadan"
    PARAMS = {"latitude": 48.85, "longitude": 2.35, "hijri_year": 1448, "method": 12}

    @responses.activate
    def test_returns_days_and_key_dates_and_caches(self, client):
        responses.add(responses.GET, f"{aladhan.settings.ALADHAN_API_BASE_URL}/hijriCalendar/1448/9",
                      json=_month(), status=200)
        r = client.get(reverse(self.URL), self.PARAMS)
        assert r.status_code == 200
        body = r.json()
        assert body["days_count"] == 29 and body["start_date"] == "2027-02-08"
        assert body["days"][0]["imsak"] == "06:10" and body["days"][0]["maghrib"] == "18:00"
        assert any(k["id"] == "laylat-al-qadr" for k in body["key_dates"])
        client.get(reverse(self.URL), self.PARAMS)
        assert len(responses.calls) == 1  # 2e appel servi par le cache

    @responses.activate
    def test_stale_when_aladhan_down(self, client):
        responses.add(responses.GET, f"{aladhan.settings.ALADHAN_API_BASE_URL}/hijriCalendar/1448/9",
                      json=_month(), status=200)
        client.get(reverse(self.URL), self.PARAMS)
        cache.delete("ramadan:1448:48.85:2.35:12:standard")
        responses.replace(responses.GET, f"{aladhan.settings.ALADHAN_API_BASE_URL}/hijriCalendar/1448/9",
                          status=500)
        r = client.get(reverse(self.URL), self.PARAMS)
        assert r.status_code == 200 and r.json()["stale"] is True

    @responses.activate
    def test_503_without_cache(self, client):
        responses.add(responses.GET, f"{aladhan.settings.ALADHAN_API_BASE_URL}/hijriCalendar/1448/9",
                      status=500)
        assert client.get(reverse(self.URL), self.PARAMS).status_code == 503

    def test_validation(self, client):
        assert client.get(reverse(self.URL)).status_code == 400
        assert client.get(reverse(self.URL), {**self.PARAMS, "hijri_year": 9}).status_code == 400
        assert client.get(reverse(self.URL), {**self.PARAMS, "madhhab": "x"}).status_code == 400
