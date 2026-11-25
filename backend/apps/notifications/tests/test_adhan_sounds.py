"""
Tests de la fonctionnalité « sons d'Adhan » :
- catalogue adhan_sounds (get_sound, get_sound_url, as_list)
- endpoint GET /notifications/adhan-sounds/ (public)
- préférence utilisateur adhan_sound_id (PUT /auth/preferences/, validation)
- payload push incluant sound_url (notification de test + tâche Celery)
"""
import pytest
from django.urls import reverse
from unittest.mock import patch

from apps.accounts.models import UserPreference
from apps.notifications import adhan_sounds
from apps.notifications.models import PushSubscription
from apps.notifications.services.push import build_payload
from apps.notifications.tasks import send_prayer_notification

pytestmark = pytest.mark.django_db

SOUNDS_URL = "/api/v1/notifications/adhan-sounds/"
PREFS_URL = "/api/v1/auth/preferences/"


# ---------------------------------------------------------------------------
# Catalogue (unitaire)
# ---------------------------------------------------------------------------
class TestAdhanSoundCatalog:
    def test_catalogue_contains_expected_sounds(self):
        assert len(adhan_sounds.SOUNDS) == 7
        reciters = {s.reciter for s in adhan_sounds.SOUNDS}
        assert {"Abdul Basit Abdus Samad", "Mishary Rashid Alafasy",
                "Muhammad Siddiq Al-Minshawi"} <= reciters
        assert {s.id for s in adhan_sounds.SOUNDS} >= {"makkah", "madinah", "alaqsa", "egypt"}

    def test_every_sound_file_exists(self):
        from pathlib import Path
        root = next((p / "frontend" / "public" for p in Path(__file__).resolve().parents
                     if (p / "frontend" / "public").is_dir()), None)
        if root is None:
            pytest.skip("dossier frontend absent (exécution dans le conteneur backend)")
        missing = [s.url for s in adhan_sounds.SOUNDS if not (root / s.url.lstrip("/")).exists()]
        assert not missing, missing

    def test_ids_are_unique(self):
        ids = [s.id for s in adhan_sounds.SOUNDS]
        assert len(ids) == len(set(ids))

    def test_get_sound_known_and_unknown(self):
        assert adhan_sounds.get_sound("alafasy").reciter == "Mishary Rashid Alafasy"
        assert adhan_sounds.get_sound("inconnu") is None
        assert adhan_sounds.get_sound(None) is None
        assert adhan_sounds.get_sound("") is None

    def test_get_sound_url_falls_back_to_default(self):
        default_url = adhan_sounds.get_sound(adhan_sounds.DEFAULT_SOUND_ID).url
        assert adhan_sounds.get_sound_url(None) == default_url
        assert adhan_sounds.get_sound_url("inconnu") == default_url
        assert adhan_sounds.get_sound_url("minshawi") == "/adhan/minshawi.mp3"


# ---------------------------------------------------------------------------
# Endpoint du catalogue
# ---------------------------------------------------------------------------
class TestAdhanSoundsEndpoint:
    def test_public_and_shape(self, api_client):
        resp = api_client.get(SOUNDS_URL)
        assert resp.status_code == 200
        assert resp.data["default"] == adhan_sounds.DEFAULT_SOUND_ID
        sounds = resp.data["sounds"]
        assert len(sounds) == 7
        for sound in sounds:
            assert set(sound.keys()) == {"id", "name", "reciter", "url"}
            assert sound["url"].startswith("/adhan/")


# ---------------------------------------------------------------------------
# Préférence utilisateur (adhan_sound_id)
# ---------------------------------------------------------------------------
class TestAdhanSoundPreference:
    def test_preference_saved(self, auth_client):
        resp = auth_client.put(PREFS_URL, {"adhan_sound_id": "alafasy"}, format="json")
        assert resp.status_code == 200, resp.data
        assert resp.data["adhan_sound_id"] == "alafasy"
        assert UserPreference.objects.get(user__email="test@example.com").adhan_sound_id == "alafasy"

    def test_preference_invalid_id_rejected(self, auth_client):
        resp = auth_client.put(PREFS_URL, {"adhan_sound_id": "inconnu"}, format="json")
        assert resp.status_code == 400
        assert "error" in resp.data

    def test_preference_empty_clears(self, auth_client, preference):
        preference.adhan_sound_id = "alafasy"
        preference.save()
        resp = auth_client.put(PREFS_URL, {"adhan_sound_id": ""}, format="json")
        assert resp.status_code == 200
        assert resp.data["adhan_sound_id"] in (None, "")


# ---------------------------------------------------------------------------
# Payload push
# ---------------------------------------------------------------------------
class TestPushPayloadSound:
    def test_build_payload_includes_sound_url(self):
        payload = build_payload("dhuhr", sound_url="/adhan/alafasy.mp3")
        assert payload["data"]["sound_url"] == "/adhan/alafasy.mp3"
        assert payload["data"]["prayer"] == "dhuhr"

    def test_build_payload_without_sound(self):
        payload = build_payload("isha")
        assert payload["data"]["sound_url"] is None

    @patch("apps.notifications.tasks.send_push")
    def test_task_uses_preferred_sound(self, mock_push, user, preference):
        """La tâche Celery joue le son choisi par l'utilisateur."""
        preference.notifications_enabled = True
        preference.adhan_sound_id = "alafasy"
        preference.save()
        PushSubscription.objects.create(
            user=user, endpoint="https://push.example.com/1", p256dh="key", auth="auth"
        )
        send_prayer_notification(user.id, "dhuhr", "2026-11-18")
        payload = mock_push.call_args[0][1]
        assert payload["data"]["sound_url"] == "/adhan/alafasy.mp3"

    @patch("apps.notifications.tasks.send_push")
    def test_task_unknown_sound_falls_back_to_default(self, mock_push, user, preference):
        """Préférence pointant vers un son retiré du catalogue → son par défaut."""
        preference.notifications_enabled = True
        preference.adhan_sound_id = "son-retire"
        preference.save()
        PushSubscription.objects.create(
            user=user, endpoint="https://push.example.com/1", p256dh="key", auth="auth"
        )
        send_prayer_notification(user.id, "dhuhr", "2026-11-18")
        payload = mock_push.call_args[0][1]
        assert payload["data"]["sound_url"] == adhan_sounds.get_sound_url(
            adhan_sounds.DEFAULT_SOUND_ID
        )
