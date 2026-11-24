"""
Tests de l'app tools :
- calcul de la Qibla (grand cercle) : cas connus, symétries, bornes
- conversion hégirienne (hijridate, Umm al-Qura)
- endpoints publics et format d'erreur
"""
from datetime import date

import pytest

from apps.tools.services import hijri as hijri_service
from apps.tools.services import qibla as qibla_service

pytestmark = pytest.mark.django_db


class TestQiblaCalculation:
    def test_from_makkah_itself(self):
        """Depuis La Mecque, le cap n'a pas de sens absolu mais doit être défini."""
        direction = qibla_service.qibla_direction(21.4225, 39.8262)
        assert 0 <= direction < 360

    def test_from_paris_is_south_east(self):
        """Depuis Paris, la Qibla est au sud-est (~119°)."""
        direction = qibla_service.qibla_direction(48.8566, 2.3522)
        assert 110 <= direction <= 130

    def test_from_new_york_is_north_east(self):
        """Depuis New York, la Qibla est au nord-est (~58°)."""
        direction = qibla_service.qibla_direction(40.7128, -74.0060)
        assert 50 <= direction <= 66

    def test_from_jakarta_is_northwest(self):
        """Depuis Jakarta (Indonésie), la Qibla est au nord-ouest (~292°)."""
        direction = qibla_service.qibla_direction(-6.2088, 106.8456)
        assert 285 <= direction <= 300

    def test_bearing_always_in_0_360(self):
        """Le cap est normalisé dans [0, 360[ quel que soit le point."""
        for lat, lng in [(-33.9249, 18.4241), (55.7558, 37.6173), (-78.0, 166.0)]:
            assert 0 <= qibla_service.qibla_direction(lat, lng) < 360

    def test_distance_from_makkah_is_zero(self):
        distance = qibla_service.kaaba_distance_km(21.4225, 39.8262)
        assert distance < 1

    def test_distance_from_paris_reasonable(self):
        """Paris-Mecque ≈ 4 600 km (plage large pour tolérance de rayon)."""
        distance = qibla_service.kaaba_distance_km(48.8566, 2.3522)
        assert 4400 <= distance <= 4800

    def test_compass_point(self):
        assert qibla_service.compass_point(0) == "N"
        assert qibla_service.compass_point(90) == "E"
        assert qibla_service.compass_point(180) == "S"
        assert qibla_service.compass_point(270) == "W"
        assert qibla_service.compass_point(350) == "N"


class TestHijriConversion:
    def test_known_date(self):
        """1er muharram 1447 ≈ 26 juin 2025 (calendrier Umm al-Qura)."""
        hijri = hijri_service.gregorian_to_hijri(date(2025, 6, 26))
        assert hijri["day"] == "1"
        assert hijri["year"] == "1447"
        assert hijri["month"]["number"] == 1

    def test_format_structure(self):
        hijri = hijri_service.gregorian_to_hijri(date(2026, 11, 17))
        assert set(hijri) == {"date", "day", "year", "month"}
        assert set(hijri["month"]) == {"number", "name", "name_ar"}
        assert hijri["date"].count("-") == 2

    def test_round_trip_consistency(self):
        """Deux dates adjacentes donnent des mois/jours hégiriens cohérents."""
        h1 = hijri_service.gregorian_to_hijri(date(2026, 11, 17))
        h2 = hijri_service.gregorian_to_hijri(date(2026, 11, 18))
        assert int(h2["day"]) - int(h1["day"]) in (0, 1, -29, -30)  # changement de mois possible


class TestQiblaEndpoint:
    URL = "/api/v1/qibla/"

    def test_qibla_public(self, api_client):
        resp = api_client.get(self.URL, {"lat": 48.8566, "lng": 2.3522})
        assert resp.status_code == 200
        assert 110 <= resp.data["qibla_direction"] <= 130
        assert resp.data["compass_point"] == "SE"
        assert resp.data["kaaba_distance_km"] > 4000

    def test_qibla_missing_params(self, api_client):
        resp = api_client.get(self.URL)
        assert resp.status_code == 400
        assert resp.data["error"]["code"] == "invalid_params"

    def test_qibla_out_of_bounds(self, api_client):
        resp = api_client.get(self.URL, {"lat": 95, "lng": 0})
        assert resp.status_code == 400
        assert resp.data["error"]["code"] == "invalid_params"

    def test_qibla_non_numeric(self, api_client):
        resp = api_client.get(self.URL, {"lat": "abc", "lng": 0})
        assert resp.status_code == 400
        assert resp.data["error"]["code"] == "invalid_params"


class TestHijriEndpoint:
    URL = "/api/v1/hijri/"

    def test_hijri_with_date(self, api_client):
        resp = api_client.get(self.URL, {"date": "2025-06-26"})
        assert resp.status_code == 200
        assert resp.data["hijri_date"]["year"] == "1447"
        assert resp.data["hijri_date"]["month"]["number"] == 1
        assert resp.data["gregorian_date"] == "2025-06-26"

    def test_hijri_without_date_defaults_today(self, api_client):
        resp = api_client.get(self.URL)
        assert resp.status_code == 200
        assert resp.data["gregorian_date"] == date.today().strftime("%Y-%m-%d")

    def test_hijri_invalid_date(self, api_client):
        resp = api_client.get(self.URL, {"date": "17/11/2026"})
        assert resp.status_code == 400
        assert resp.data["error"]["code"] == "invalid_date"
