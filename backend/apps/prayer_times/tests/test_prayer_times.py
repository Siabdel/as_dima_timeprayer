"""
Tests de l'app prayer_times :
- normalisation de la réponse Aladhan
- cache Redis (hit/miss, ne jamais rappeler Aladhan)
- stale-while-revalidate (Aladhan en panne → données périmées + Warning)
- validation des paramètres
- endpoint /today/ (JWT, lieu par défaut)
"""
from datetime import datetime, timedelta
from unittest.mock import patch

import pytest
import responses
from django.core.cache import cache
from django.urls import reverse
from rest_framework import status

from apps.locations.models import Location
from apps.prayer_times.services import aladhan, cache as prayer_cache

pytestmark = pytest.mark.django_db

# Payload Aladhan minimal (structure réelle simplifiée)
ALADHAN_PAYLOAD = {
    "status": "OK",
    "data": {
        "timings": {
            "Fajr": "05:23 (+01:00)",
            "Sunrise": "06:45 (+01:00)",
            "Dhuhr": "12:30 (+01:00)",
            "Asr": "15:45 (+01:00)",
            "Maghrib": "18:12 (+01:00)",
            "Isha": "19:30 (+01:00)",
        },
        "date": {
            "hijri": {
                "date": "17-05-1447",
                "day": "17",
                "year": "1447",
                "month": {"number": 5, "en": "Jumada al-Ula", "ar": "جمادى الأولى"},
            },
            "gregorian": {"date": "17-11-2026"},
        },
        "meta": {"timezone": "Europe/Paris"},
    },
}


@pytest.fixture(autouse=True)
def clean_cache():
    """Cache vidé avant et après chaque test (isolation totale)."""
    cache.clear()
    yield
    cache.clear()


def _mock_aladhan(body=None, status_code=200):
    """Enregistre le mock de l'endpoint Aladhan par coordonnées.

    La date du mock est calculée dynamiquement (aujourd'hui, UTC) : la vue
    appelle Aladhan avec la date courante — un mock figé casserait les tests
    à chaque changement de jour (comme les 4 échecs du 18-11-2026).
    """
    from django.utils import timezone as dj_tz

    today = dj_tz.now().strftime("%d-%m-%Y")
    responses.add(
        responses.GET,
        f"{aladhan.settings.ALADHAN_API_BASE_URL}/timings/{today}",
        json=body or ALADHAN_PAYLOAD,
        status=status_code,
    )


class TestNormalization:
    def test_normalize_payload(self):
        data = aladhan._normalize_payload(ALADHAN_PAYLOAD["data"])
        assert data["fajr"] == "05:23"          # suffixe (+01:00) supprimé
        assert data["sunrise"] == "06:45"
        assert data["dhuhr"] == "12:30"
        assert data["asr"] == "15:45"
        assert data["maghrib"] == "18:12"
        assert data["isha"] == "19:30"
        assert data["timezone"] == "Europe/Paris"
        assert data["hijri_date"]["date"] == "17-05-1447"
        assert data["hijri_date"]["month"]["number"] == 5
        assert data["hijri_date"]["month"]["name"] == "Jumada al-Ula"
        assert data["hijri_date"]["month"]["name_ar"] == "جمادى الأولى"

    def test_clean_timing_variants(self):
        assert aladhan._clean_timing("05:23") == "05:23"
        assert aladhan._clean_timing("05:23 (+02:00)") == "05:23"
        assert aladhan._clean_timing("05:23 (CEST)") == "05:23"


class TestCacheKey:
    def test_key_with_coords(self):
        key = prayer_cache.build_cache_key(
            latitude=48.8566, longitude=2.3522, date_iso="2026-11-17",
            method=3, madhhab="standard",
        )
        # Coordonnées arrondies à 2 décimales
        assert key == "prayer:48.86:2.35:2026-11-17:3:standard"

    def test_key_with_city(self):
        key = prayer_cache.build_cache_key(
            city="Paris", country="France", date_iso="2026-11-17",
            method=3, madhhab="standard",
        )
        assert key == "prayer:paris:france:2026-11-17:3:standard"

    def test_same_coords_share_cache(self):
        # 48.8566 et 48.8580 s'arrondissent tous deux à 48.86 → même clé
        k1 = prayer_cache.build_cache_key(
            latitude=48.8566, longitude=2.3522, date_iso="2026-11-17",
            method=3, madhhab="standard",
        )
        k2 = prayer_cache.build_cache_key(
            latitude=48.8580, longitude=2.3530, date_iso="2026-11-17",
            method=3, madhhab="standard",
        )
        assert k1 == k2


class TestCacheTTL:
    def test_ttl_today(self):
        # Aujourd'hui dans la timezone du lieu → TTL jusqu'à minuit (< 24 h)
        today = datetime.now().strftime("%Y-%m-%d")
        ttl = prayer_cache.compute_cache_ttl(today, "Europe/Paris")
        assert 0 < ttl <= 24 * 3600

    def test_ttl_default_for_future_date(self):
        future = (datetime.now() + timedelta(days=5)).strftime("%Y-%m-%d")
        ttl = prayer_cache.compute_cache_ttl(future, "Europe/Paris")
        assert ttl == 24 * 3600

    def test_ttl_default_with_invalid_timezone(self):
        ttl = prayer_cache.compute_cache_ttl("2026-11-17", "Zone/Inconnue")
        assert ttl == 24 * 3600


class TestPrayerTimesEndpoint:
    URL = "/api/v1/prayer-times/"

    @responses.activate
    def test_first_call_fetches_aladhan(self, api_client):
        _mock_aladhan()
        resp = api_client.get(self.URL, {"latitude": 48.8566, "longitude": 2.3522})
        assert resp.status_code == 200, resp.data
        assert resp.data["fajr"] == "05:23"
        assert resp.data["timezone"] == "Europe/Paris"
        assert resp.data["stale"] is False
        assert resp.data["location"]["latitude"] == 48.8566
        assert len(responses.calls) == 1

    @responses.activate
    def test_second_call_served_from_cache(self, api_client):
        """La deuxième requête ne doit JAMAIS rappeler Aladhan."""
        _mock_aladhan()
        api_client.get(self.URL, {"latitude": 48.8566, "longitude": 2.3522})
        resp = api_client.get(self.URL, {"latitude": 48.8566, "longitude": 2.3522})
        assert resp.status_code == 200
        assert len(responses.calls) == 1  # Aladhan appelé une seule fois

    @responses.activate
    def test_stale_while_revalidate(self, api_client):
        """Aladhan en panne + entrée périmée → données stale + header Warning."""
        _mock_aladhan()
        resp = api_client.get(self.URL, {"latitude": 48.8566, "longitude": 2.3522})
        assert resp.status_code == 200

        # Simule l'expiration de la clé principale (la sauvegarde reste valide)
        from django.utils import timezone as dj_tz

        key = prayer_cache.build_cache_key(
            latitude=48.8566, longitude=2.3522,
            date_iso=dj_tz.now().strftime("%Y-%m-%d"),
            method=3, madhhab="standard",
        )
        cache.delete(key)

        # Aladhan tombe en panne
        responses.reset()
        _mock_aladhan(status_code=500)

        resp = api_client.get(self.URL, {"latitude": 48.8566, "longitude": 2.3522})
        assert resp.status_code == 200
        assert resp.data["stale"] is True
        assert "Warning" in resp.headers
        assert resp.data["fajr"] == "05:23"  # données périmées servies

    @responses.activate
    def test_aladhan_down_without_stale(self, api_client):
        """Aladhan en panne sans sauvegarde → 503 avec format d'erreur."""
        _mock_aladhan(status_code=500)
        resp = api_client.get(self.URL, {"latitude": 48.8566, "longitude": 2.3522})
        assert resp.status_code == 503
        assert resp.data["error"]["code"] == "external_api_error"

    def test_invalid_params_no_location(self, api_client):
        resp = api_client.get(self.URL)
        assert resp.status_code == 400
        assert resp.data["error"]["code"] == "invalid_params"

    def test_invalid_madhhab(self, api_client):
        resp = api_client.get(
            self.URL, {"latitude": 48.85, "longitude": 2.35, "madhhab": "maliki"}
        )
        assert resp.status_code == 400
        assert resp.data["error"]["code"] == "invalid_madhhab"

    def test_invalid_date(self, api_client):
        resp = api_client.get(
            self.URL, {"latitude": 48.85, "longitude": 2.35, "date": "17/11/2026"}
        )
        assert resp.status_code == 400
        assert resp.data["error"]["code"] == "invalid_date"

    def test_invalid_coordinates(self, api_client):
        resp = api_client.get(self.URL, {"latitude": 120, "longitude": 2.35})
        assert resp.status_code == 400
        assert resp.data["error"]["code"] == "invalid_params"

    @responses.activate
    def test_city_country_mode(self, api_client):
        responses.add(
            responses.GET,
            f"{aladhan.settings.ALADHAN_API_BASE_URL}/timingsByCity",
            json=ALADHAN_PAYLOAD,
            status=200,
        )
        resp = api_client.get(self.URL, {"city": "Paris", "country": "France"})
        assert resp.status_code == 200
        assert resp.data["location"]["city"] == "Paris"
        assert len(responses.calls) == 1


class TestTodayEndpoint:
    URL = "/api/v1/prayer-times/today/"

    def test_requires_auth(self, api_client):
        resp = api_client.get(self.URL)
        assert resp.status_code == 401
        assert resp.data["error"]["code"] == "unauthorized"

    def test_no_default_location(self, auth_client):
        resp = auth_client.get(self.URL)
        assert resp.status_code == 400
        assert resp.data["error"]["code"] == "no_default_location"

    @responses.activate
    def test_today_with_default_location(self, auth_client, user):
        location = Location.objects.create(
            user=user, label="Maison", latitude=48.8566, longitude=2.3522,
            city="Paris", country="France", is_default=True,
        )
        from apps.accounts.models import UserPreference
        prefs, _ = UserPreference.objects.get_or_create(user=user)
        prefs.default_location = location
        prefs.save()

        _mock_aladhan()
        resp = auth_client.get(self.URL)
        assert resp.status_code == 200, resp.data
        assert resp.data["fajr"] == "05:23"
        assert resp.data["location"]["label"] == "Maison"
