"""
Tâches Celery de l'app notifications (file "notifications").

Idempotence : chaque couple (utilisateur, prière, date) est notifié une
seule fois — garanti par le journal PrayerNotificationLog (contrainte
d'unicité) et par une clé de déduplication Redis.

Planification : la tâche `scan_prayer_notifications` est exécutée par Celery
Beat toutes les 5 minutes. Elle compare l'heure locale de chaque utilisateur
aux horaires du jour (issus du cache Aladhan) et déclenche l'envoi pour les
prières qui viennent de sonner.
"""
import logging
from datetime import datetime, timedelta, time
from zoneinfo import ZoneInfo

from celery import shared_task
from django.conf import settings
from django.core.cache import cache
from django.utils import timezone as dj_timezone

from apps.accounts.models import UserPreference
from apps.prayer_times.services import cache as prayer_cache

from . import adhan_sounds
from .models import PrayerNotificationLog, PushSubscription
from .services.push import (
    GoneSubscriptionError,
    PushSendError,
    build_payload,
    send_push,
)

logger = logging.getLogger(__name__)

# Fenêtre de déclenchement : une prière est notifiée si l'heure actuelle du
# lieu est dans [heure de la prière, heure + SCAN_INTERVAL].
SCAN_INTERVAL = timedelta(minutes=5)

# Prières notifiables (dans l'ordre du jour).
PRAYERS = ("fajr", "sunrise", "dhuhr", "asr", "maghrib", "isha")


def _in_quiet_hours(now_local: datetime, prefs: UserPreference) -> bool:
    """L'heure `now_local` est-elle dans la fenêtre calme de l'utilisateur ?"""
    start, end = prefs.quiet_hours_start, prefs.quiet_hours_end
    if start is None or end is None:
        return False
    # Django retourne des objets time en base ; les instances non sauvées
    # (tests) portent des chaînes : normalisation défensive.
    if isinstance(start, str):
        start = time.fromisoformat(start)
    if isinstance(end, str):
        end = time.fromisoformat(end)
    current = now_local.time()
    if start <= end:
        return start <= current < end
    # Fenêtre traversant minuit (ex. 22:00 -> 06:00)
    return current >= start or current < end


def _next_prayer_due(timings: dict, now_local: datetime) -> str | None:
    """
    Retourne la prière qui vient de sonner (dans la fenêtre de scan), ou None.
    `timings` contient les heures "HH:MM" dans la timezone du lieu.
    """
    for prayer in PRAYERS:
        if not timings:
            return None
        time_str = timings.get(prayer)
        if not time_str:
            continue
        hour, minute = map(int, time_str.split(":")[:2])
        due_at = now_local.replace(hour=hour, minute=minute, second=0, microsecond=0)
        if due_at <= now_local < due_at + SCAN_INTERVAL:
            return prayer
    return None


@shared_task(bind=True, max_retries=3, default_retry_delay=30)
def send_prayer_notification(self, user_id: int, prayer_name: str, date_iso: str) -> str:
    """
    Envoie la notification Adhan d'une prière à un utilisateur.

    Idempotent : vérifie le journal avant tout envoi. Respecte les préférences
    (notifications par prière, heures calmes). Supprime les abonnements 410.
    """
    date_obj = datetime.strptime(date_iso, "%Y-%m-%d").date()

    # --- Idempotence : déjà traitée pour ce couple user/prière/date ? -------
    log, created = PrayerNotificationLog.objects.get_or_create(
        user_id=user_id, prayer_name=prayer_name, date=date_obj,
        defaults={"status": PrayerNotificationLog.STATUS_SENT},
    )
    if not created:
        return f"already-logged:{log.status}"

    try:
        prefs = UserPreference.objects.select_related("user").get(user_id=user_id)
    except UserPreference.DoesNotExist:
        log.status = PrayerNotificationLog.STATUS_SKIPPED_DISABLED
        log.save(update_fields=["status"])
        return "skipped:no-preferences"

    # --- Préférences : notifications globales + par prière -------------------
    if not prefs.is_prayer_enabled(prayer_name):
        log.status = PrayerNotificationLog.STATUS_SKIPPED_DISABLED
        log.save(update_fields=["status"])
        return "skipped:preference-disabled"

    # --- Heures calmes --------------------------------------------------------
    tz_name = prefs.default_location.timezone if prefs.default_location else "UTC"
    try:
        tz = ZoneInfo(tz_name)
    except Exception:
        tz = ZoneInfo("UTC")
    now_local = dj_timezone.now().astimezone(tz)
    if _in_quiet_hours(now_local, prefs):
        log.status = PrayerNotificationLog.STATUS_SKIPPED_QUIET
        log.save(update_fields=["status"])
        return "skipped:quiet-hours"

    # --- Envoi à tous les abonnements ------------------------------------------
    subscriptions = list(PushSubscription.objects.filter(user_id=user_id))
    if not subscriptions:
        log.status = PrayerNotificationLog.STATUS_SKIPPED_NO_SUB
        log.save(update_fields=["status"])
        return "skipped:no-subscription"

    payload = build_payload(
        prayer_name, sound_url=adhan_sounds.get_sound_url(prefs.adhan_sound_id)
    )
    sent, gone = 0, 0
    for subscription in subscriptions:
        try:
            send_push(subscription, payload)
            sent += 1
        except GoneSubscriptionError:
            # Abonnement expiré côté navigateur : suppression définitive.
            subscription.delete()
            gone += 1
        except PushSendError:
            continue  # erreur transitoire : les autres abonnements continuent

    log.sent_at = dj_timezone.now()
    log.save(update_fields=["sent_at"])
    return f"sent:{sent},gone:{gone}"


@shared_task
def scan_prayer_notifications() -> dict:
    """
    Tâche périodique (Celery Beat) : scanne les utilisateurs dont les
    notifications sont activées et déclenche l'envoi des prières qui viennent
    de sonner dans leur fuseau horaire.
    """
    now_utc = dj_timezone.now()
    triggered = []

    for prefs in (
        UserPreference.objects.filter(notifications_enabled=True)
        .select_related("user", "default_location")
    ):
        location = prefs.default_location
        if location is None:
            continue

        tz_name = location.timezone or "UTC"
        try:
            tz = ZoneInfo(tz_name)
        except Exception:
            tz = ZoneInfo("UTC")

        date_iso = now_utc.astimezone(tz).strftime("%Y-%m-%d")

        # Horaires du jour — servis depuis le cache Redis (jamais d'appel
        # Aladhan depuis le scanner) ; si absents, le scan attendra le
        # prochain passage (la clé sera remplie par une requête utilisateur).
        key = prayer_cache.build_cache_key(
            latitude=float(location.latitude), longitude=float(location.longitude),
            date_iso=date_iso, method=prefs.calculation_method or 3,
            madhhab=prefs.madhhab,
        )
        timings = prayer_cache.get_cached(key)
        if not timings:
            continue

        now_local = now_utc.astimezone(tz)
        prayer = _next_prayer_due(timings, now_local)
        if prayer is None:
            continue

        # Déduplication Redis (sécurité supplémentaire en cas de race entre
        # deux workers) : SETNX avec TTL de 10 minutes.
        dedup_key = f"notif-dedup:{prefs.user_id}:{prayer}:{date_iso}"
        if not cache.add(dedup_key, "1", timeout=600):
            continue

        send_prayer_notification.delay(prefs.user_id, prayer, date_iso)
        triggered.append({"user": prefs.user_id, "prayer": prayer})

    return {"triggered": triggered}
