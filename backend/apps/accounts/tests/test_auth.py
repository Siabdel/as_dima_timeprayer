"""Tests des endpoints d'authentification et des préférences."""
import pytest
from django.urls import reverse

pytestmark = pytest.mark.django_db

REGISTER_URL = "/api/v1/auth/register/"
TOKEN_URL = "/api/v1/auth/token/"
REFRESH_URL = "/api/v1/auth/token/refresh/"
ME_URL = "/api/v1/auth/me/"
PREFS_URL = "/api/v1/auth/preferences/"

VALID_REGISTER = {
    "email": "ali@example.com",
    "password": "UnMotDePasseSolide1!",
    "password2": "UnMotDePasseSolide1!",
    "first_name": "Ali",
    "last_name": "Ben Salah",
}


class TestRegister:
    def test_register_creates_user(self, api_client):
        resp = api_client.post(REGISTER_URL, VALID_REGISTER, format="json")
        assert resp.status_code == 201, resp.data
        assert resp.data["email"] == "ali@example.com"
        from apps.accounts.models import User
        assert User.objects.filter(email="ali@example.com").exists()

    def test_register_password_mismatch(self, api_client):
        payload = {**VALID_REGISTER, "password2": "AutreMotDePasse1!"}
        resp = api_client.post(REGISTER_URL, payload, format="json")
        assert resp.status_code == 400
        assert resp.data["error"]["code"] == "validation_error"
        assert "password2" in resp.data["error"]["details"]

    def test_register_duplicate_email(self, api_client, user):
        payload = {**VALID_REGISTER, "email": user.email}
        resp = api_client.post(REGISTER_URL, payload, format="json")
        assert resp.status_code == 400

    def test_register_weak_password(self, api_client):
        payload = {**VALID_REGISTER, "password": "123", "password2": "123"}
        resp = api_client.post(REGISTER_URL, payload, format="json")
        assert resp.status_code == 400


class TestToken:
    def test_login_returns_tokens(self, api_client, user):
        resp = api_client.post(
            TOKEN_URL, {"email": user.email, "password": "UnMotDePasseSolide1!"},
            format="json",
        )
        assert resp.status_code == 200
        assert "access" in resp.data and "refresh" in resp.data

    def test_login_wrong_password(self, api_client, user):
        resp = api_client.post(
            TOKEN_URL, {"email": user.email, "password": "MauvaisMot1!"},
            format="json",
        )
        assert resp.status_code == 401
        # Format d'erreur normalisé {"error": {code, message}}
        assert resp.data["error"]["code"] == "unauthorized"

    def test_refresh_returns_new_access(self, api_client, user):
        tokens = api_client.post(
            TOKEN_URL, {"email": user.email, "password": "UnMotDePasseSolide1!"},
            format="json",
        ).data
        resp = api_client.post(REFRESH_URL, {"refresh": tokens["refresh"]}, format="json")
        assert resp.status_code == 200
        assert "access" in resp.data


class TestMe:
    def test_me_requires_auth(self, api_client):
        resp = api_client.get(ME_URL)
        assert resp.status_code == 401
        assert resp.data["error"]["code"] == "unauthorized"

    def test_me_returns_user(self, auth_client, user):
        resp = auth_client.get(ME_URL)
        assert resp.status_code == 200
        assert resp.data["email"] == user.email

    def test_me_patch_updates_name(self, auth_client):
        resp = auth_client.patch(ME_URL, {"first_name": "Nouveau"}, format="json")
        assert resp.status_code == 200
        assert resp.data["first_name"] == "Nouveau"


class TestPreferences:
    def test_preferences_created_on_first_get(self, auth_client):
        resp = auth_client.get(PREFS_URL)
        assert resp.status_code == 200
        # Valeurs par défaut
        assert resp.data["notifications_enabled"] is False
        assert resp.data["fajr"] is True
        assert resp.data["madhhab"] == "standard"

    def test_preferences_put_updates(self, auth_client):
        resp = auth_client.put(
            PREFS_URL,
            {
                "notifications_enabled": True,
                "dhuhr": False,
                "madhhab": "hanafi",
                "calculation_method": 2,
                "quiet_hours_start": "22:00",
                "quiet_hours_end": "06:00",
            },
            format="json",
        )
        assert resp.status_code == 200
        assert resp.data["notifications_enabled"] is True
        assert resp.data["dhuhr"] is False
        assert resp.data["madhhab"] == "hanafi"

    def test_preferences_requires_auth(self, api_client):
        resp = api_client.get(PREFS_URL)
        assert resp.status_code == 401


class TestSettingsPreferences:
    URL = "/api/v1/auth/preferences/"

    def _auth(self, api_client, django_user_model):
        user = django_user_model.objects.create_user(email="s@example.com", password="Passw0rd!xyz")
        api_client.force_authenticate(user)
        return user

    def test_new_fields_roundtrip(self, api_client, django_user_model):
        self._auth(api_client, django_user_model)
        resp = api_client.put(self.URL, {
            "timezone_mode": "manual", "timezone": "Africa/Casablanca", "language": "en",
            "alert_modes": {"fajr": "vibrate", "isha": "silent"},
            "reminder_minutes_before": 10, "fajr_adhan_sound_id": "alafasy",
            "adhan_volume": 60, "adhan_fade_in": True,
        }, format="json")
        assert resp.status_code == 200, resp.data
        assert resp.data["timezone"] == "Africa/Casablanca"
        assert resp.data["alert_modes"]["isha"] == "silent"

    def test_invalid_values_rejected(self, api_client, django_user_model):
        self._auth(api_client, django_user_model)
        for bad in (
            {"timezone": "Mars/Olympus"},
            {"alert_modes": {"fajr": "loud"}},
            {"reminder_minutes_before": 7},
            {"fajr_adhan_sound_id": "nope"},
            {"adhan_volume": 150},
        ):
            assert api_client.put(self.URL, bad, format="json").status_code == 400, bad
