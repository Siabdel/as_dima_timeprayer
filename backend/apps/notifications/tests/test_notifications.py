"""
Tests de l'app notifications :
- planification des notifications (fenêtre de scan, timezone du lieu)
- idempotence (pas de double envoi pour user/prière/date)
- respect des préférences (notifications désactivées, heures calmes)
- suppression des abonnements 410 (Gone)
- endpoints d'abonnement (subscribe/unsubscribe/status)
"""
from datetime import datetime, timedelta
from unittest.mock import patch

import pytest
from django.core.cache import cache
from django.urls import reverse
from rest_framework import status

from apps.accounts.models import UserPreference
from apps.locations.models import Location
from apps.notifications.models import PrayerNotificationLog, PushSubscription
from apps.notifications.tasks import (
    _in_quiet_hours,
    _next_prayer_due,
    scan_prayer_notifications,
    send_prayer_notification,
)

pytestmark = pytest.mark.django_db

TIMINGS = {
    "fajr": "05:23", "sunrise": "06:45", "dhuhr": "12:30",
    "asr": "15:45", "maghrib": "18:12", "isha": "19:30",
}


@pytest.fixture(autouse=True)
def clean_cache():
    cache.clear()
    yield
    cache.clear()


@pytest.fixture
def enabled_user_location(user, preference):
    """Utilisateur avec notifications activées et lieu par défaut à Paris."""
    location = Location.objects.create(
        user=user, label="Paris", latitude=48.8566, longitude=2.3522,
        timezone="Europe/Paris", is_default=True,
    )
    preference.notifications_enabled = True
    preference.default_location = location
    preference.save()
    return location


class TestHelpers:
    def test_next_prayer_due_in_window(self):
        """12:33 : Dhuhr (12:30) est dans la fenêtre de scan [12:30, 12:35)."""
        now = datetime(2026, 11, 17, 12, 33, 0)
        assert _next_prayer_due(TIMINGS, now) == "dhuhr"

    def test_next_prayer_outside_window(self):
        """12:36 : Dhuhr est passée hors fenêtre, Asr pas encore."""
        now = datetime(2026, 11, 17, 12, 36, 0)
        assert _next_prayer_due(TIMINGS, now) is None

    def test_next_prayer_before_any(self):
        now = datetime(2026, 11, 17, 5, 0, 0)
        assert _next_prayer_due(TIMINGS, now) is None

    def test_quiet_hours_same_day(self):
        prefs = UserPreference(quiet_hours_start="22:00", quiet_hours_end="06:00")
        # Cas fenêtre traversant minuit
        assert _in_quiet_hours(datetime(2026, 11, 17, 23, 0), prefs) is True
        assert _in_quiet_hours(datetime(2026, 11, 17, 2, 0), prefs) is True
        assert _in_quiet_hours(datetime(2026, 11, 17, 12, 0), prefs) is False

    def test_quiet_hours_no_window(self):
        prefs = UserPreference()
        assert _in_quiet_hours(datetime(2026, 11, 17, 12, 0), prefs) is False


class TestSendPrayerNotification:
    DATE = "2026-11-17"

    @pytest.fixture(autouse=True)
    def enable_notifications(self, preference):
        """Tous les tests de cette classe : notifications globales activées."""
        preference.notifications_enabled = True
        preference.save()

    @patch("apps.notifications.tasks.send_push")
    def test_sends_to_subscription(self, mock_push, user, preference):
        PushSubscription.objects.create(
            user=user, endpoint="https://push.example.com/1",
            p256dh="key", auth="auth",
        )
        result = send_prayer_notification(user.id, "dhuhr", self.DATE)
        assert result == "sent:1,gone:0"
        mock_push.assert_called_once()
        log = PrayerNotificationLog.objects.get(user=user, prayer_name="dhuhr")
        assert log.status == PrayerNotificationLog.STATUS_SENT

    @patch("apps.notifications.tasks.send_push")
    def test_idempotent_second_call(self, mock_push, user, preference):
        """Deuxième appel pour le même couple user/prière/date : pas d'envoi."""
        PushSubscription.objects.create(
            user=user, endpoint="https://push.example.com/1",
            p256dh="key", auth="auth",
        )
        send_prayer_notification(user.id, "dhuhr", self.DATE)
        result = send_prayer_notification(user.id, "dhuhr", self.DATE)
        assert result.startswith("already-logged")
        assert mock_push.call_count == 1  # envoyé une seule fois

    def test_skipped_when_disabled(self, user, preference):
        """Notifications globales désactivées → skip sans envoi."""
        preference.notifications_enabled = False
        preference.save()
        result = send_prayer_notification(user.id, "dhuhr", self.DATE)
        assert result == "skipped:preference-disabled"

    def test_skipped_when_prayer_disabled(self, user, preference):
        preference.dhuhr = False
        preference.save()
        result = send_prayer_notification(user.id, "dhuhr", self.DATE)
        assert result == "skipped:preference-disabled"

    def test_skipped_no_subscription(self, user, preference):
        result = send_prayer_notification(user.id, "dhuhr", self.DATE)
        assert result == "skipped:no-subscription"

    @patch("apps.notifications.tasks.send_push")
    def test_gone_subscription_removed(self, mock_push, user, preference):
        """410 (Gone) → l'abonnement est supprimé."""
        PushSubscription.objects.create(
            user=user, endpoint="https://push.example.com/expired",
            p256dh="key", auth="auth",
        )
        from apps.notifications.services.push import GoneSubscriptionError

        mock_push.side_effect = GoneSubscriptionError()
        result = send_prayer_notification(user.id, "dhuhr", self.DATE)
        assert result == "sent:0,gone:1"
        assert not PushSubscription.objects.filter(user=user).exists()


class TestScanTask:
    @patch("apps.notifications.tasks.send_prayer_notification.delay")
    def test_triggers_when_prayer_due(self, mock_delay, user, enabled_user_location):
        """
        L'heure locale du lieu correspond à Dhuhr (fenêtre de scan) → déclenché.
        On patche dj_timezone.now pour figer le temps côté lieu.
        """
        from apps.prayer_times.services import cache as prayer_cache

        # Injecter les horaires dans le cache (le scanner ne lit QUE le cache)
        key = prayer_cache.build_cache_key(
            latitude=48.8566, longitude=2.3522, date_iso="2026-11-17",
            method=3, madhhab="standard",
        )
        prayer_cache.store(key, TIMINGS, 3600)

        # 12:33 à Paris = 11:33 UTC en hiver
        frozen = datetime(2026, 11, 17, 11, 33, 0, tzinfo=__import__("zoneinfo").ZoneInfo("UTC"))
        with patch("apps.notifications.tasks.dj_timezone.now", return_value=frozen):
            result = scan_prayer_notifications()
        assert len(result["triggered"]) == 1
        assert result["triggered"][0]["prayer"] == "dhuhr"
        mock_delay.assert_called_once_with(user.id, "dhuhr", "2026-11-17")

    @patch("apps.notifications.tasks.send_prayer_notification.delay")
    def test_no_trigger_when_no_timings(self, mock_delay, user, enabled_user_location):
        """Horaires absents du cache → le scan attend (aucun appel Aladhan)."""
        frozen = datetime(2026, 11, 17, 11, 33, 0, tzinfo=__import__("zoneinfo").ZoneInfo("UTC"))
        with patch("apps.notifications.tasks.dj_timezone.now", return_value=frozen):
            result = scan_prayer_notifications()
        assert result["triggered"] == []
        mock_delay.assert_not_called()

    @patch("apps.notifications.tasks.send_prayer_notification.delay")
    def test_no_trigger_outside_window(self, mock_delay, user, enabled_user_location):
        """12:36 (hors fenêtre) → aucun déclenchement."""
        from apps.prayer_times.services import cache as prayer_cache

        key = prayer_cache.build_cache_key(
            latitude=48.8566, longitude=2.3522, date_iso="2026-11-17",
            method=3, madhhab="standard",
        )
        prayer_cache.store(key, TIMINGS, 3600)
        frozen = datetime(2026, 11, 17, 11, 36, 0, tzinfo=__import__("zoneinfo").ZoneInfo("UTC"))
        with patch("apps.notifications.tasks.dj_timezone.now", return_value=frozen):
            result = scan_prayer_notifications()
        assert result["triggered"] == []

    @patch("apps.notifications.tasks.send_prayer_notification.delay")
    def test_dedup_redis(self, mock_delay, user, enabled_user_location):
        """Deux scans consécutifs dans la même fenêtre : un seul déclenchement."""
        from apps.prayer_times.services import cache as prayer_cache

        key = prayer_cache.build_cache_key(
            latitude=48.8566, longitude=2.3522, date_iso="2026-11-17",
            method=3, madhhab="standard",
        )
        prayer_cache.store(key, TIMINGS, 3600)
        frozen = datetime(2026, 11, 17, 11, 33, 0, tzinfo=__import__("zoneinfo").ZoneInfo("UTC"))
        with patch("apps.notifications.tasks.dj_timezone.now", return_value=frozen):
            scan_prayer_notifications()
            result = scan_prayer_notifications()
        assert result["triggered"] == []  # dédupliqué
        assert mock_delay.call_count == 1


class TestSubscriptionEndpoints:
    SUBSCRIBE_URL = "/api/v1/notifications/subscribe/"
    STATUS_URL = "/api/v1/notifications/status/"
    VAPID_URL = "/api/v1/notifications/vapid-key/"
    TEST_URL = "/api/v1/notifications/test/"

    VALID_SUB = {
        "endpoint": "https://push.example.com/abc",
        "keys": {"p256dh": "some-key", "auth": "some-auth"},
    }

    def test_subscribe_requires_auth(self, api_client):
        resp = api_client.post(self.SUBSCRIBE_URL, self.VALID_SUB, format="json")
        assert resp.status_code == 401

    def test_subscribe_creates(self, auth_client, user):
        resp = auth_client.post(self.SUBSCRIBE_URL, self.VALID_SUB, format="json")
        assert resp.status_code == 201
        assert PushSubscription.objects.filter(user=user, endpoint=self.VALID_SUB["endpoint"]).exists()

    def test_subscribe_renews_existing(self, auth_client):
        auth_client.post(self.SUBSCRIBE_URL, self.VALID_SUB, format="json")
        updated = {**self.VALID_SUB, "keys": {"p256dh": "new-key", "auth": "new-auth"}}
        resp = auth_client.post(self.SUBSCRIBE_URL, updated, format="json")
        assert resp.status_code == 200
        sub = PushSubscription.objects.get(endpoint=self.VALID_SUB["endpoint"])
        assert sub.p256dh == "new-key"

    def test_subscribe_invalid_keys(self, auth_client):
        resp = auth_client.post(
            self.SUBSCRIBE_URL,
            {"endpoint": "https://push.example.com/x", "keys": {"p256dh": "k"}},
            format="json",
        )
        assert resp.status_code == 400

    def test_unsubscribe(self, auth_client, user):
        auth_client.post(self.SUBSCRIBE_URL, self.VALID_SUB, format="json")
        resp = auth_client.delete(self.SUBSCRIBE_URL, {"endpoint": self.VALID_SUB["endpoint"]}, format="json")
        assert resp.status_code == 200
        assert not PushSubscription.objects.filter(user=user).exists()

    def test_status(self, auth_client, user):
        resp = auth_client.get(self.STATUS_URL)
        assert resp.status_code == 200
        assert resp.data["subscribed"] is False

    def test_vapid_key_public(self, api_client):
        resp = api_client.get(self.VAPID_URL)
        assert resp.status_code == 200
        assert "public_key" in resp.data

    def test_test_notification_no_subscription(self, auth_client):
        resp = auth_client.post(self.TEST_URL, {"prayer_name": "dhuhr"}, format="json")
        assert resp.status_code == 400
        assert resp.data["error"]["code"] == "no_subscription"
