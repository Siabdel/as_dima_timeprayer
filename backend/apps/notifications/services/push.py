"""
Envoi des notifications Web Push (VAPID) via pywebpush.

Les clés VAPID proviennent des variables d'environnement ; elles ne quittent
jamais le serveur. Les abonnements renvoyant 410 (Gone) — navigateur qui a
expiré l'abonnement — sont supprimés.
"""
import logging

from django.conf import settings
from pywebpush import WebPushException, webpush

logger = logging.getLogger(__name__)

PRAYER_LABELS = {
    "fajr": "Fajr",
    "sunrise": "Sunrise",
    "dhuhr": "Dhuhr",
    "asr": "Asr",
    "maghrib": "Maghrib",
    "isha": "Isha",
}


class PushSendError(Exception):
    """Échec de l'envoi d'une notification push (hors 410)."""


def send_push(subscription: "PushSubscription", payload: dict) -> None:
    """
    Envoie une notification JSON à un abonnement.

    Lève GoneSubscriptionError si le navigateur renvoie 410 : l'appelant
    doit alors supprimer l'abonnement.
    """
    payload_str = __import__("json").dumps(payload, ensure_ascii=False)

    try:
        webpush(
            subscription_info={
                "endpoint": subscription.endpoint,
                "keys": {"p256dh": subscription.p256dh, "auth": subscription.auth},
            },
            data=payload_str,
            vapid_private_key=settings.VAPID_PRIVATE_KEY,
            vapid_claims={"sub": f"mailto:{settings.VAPID_ADMIN_EMAIL}"},
        )
    except WebPushException as exc:
        response = getattr(exc, "response", None)
        if response is not None and response.status_code == 410:
            raise GoneSubscriptionError() from exc
        logger.warning("Envoi push échoué (%s) : %s", subscription.id, exc)
        raise PushSendError(str(exc)) from exc


class GoneSubscriptionError(Exception):
    """L'abonnement est expiré côté navigateur (HTTP 410) : à supprimer."""


def build_payload(
    prayer_name: str,
    sound_url: str | None = None,
    alert_mode: str = "full",
    volume: int = 100,
    fade_in: bool = False,
    reminder_minutes: int | None = None,
) -> dict:
    """
    Construit le payload JSON d'une notification Adhan.

    `sound_url` : chemin RELATIF du MP3 à jouer (catalogue adhan_sounds).
    Le service worker du client le transmet à une fenêtre ouverte de l'app,
    qui joue le son ; si aucune fenêtre n'est ouverte, seule la notification
    est affichée (limitation des navigateurs : un SW ne peut pas jouer d'audio).
    """
    label = PRAYER_LABELS.get(prayer_name, prayer_name)
    if reminder_minutes:
        body = f"{label} dans {reminder_minutes} minutes."
        tag = f"prayer-reminder-{prayer_name}"
    else:
        body = f"Il est l'heure de la prière du {label}."
        tag = f"prayer-{prayer_name}"
    return {
        "title": "🕌 Adhan",
        "body": body,
        "tag": tag,
        "data": {
            "prayer": prayer_name,
            "sound_url": sound_url,
            # full = Adhan complet, beep = bip court, vibrate, silent
            "alert_mode": alert_mode,
            "volume": volume,
            "fade_in": fade_in,
        },
    }


RAMADAN_KINDS = {
    "imsak": ("🌙 Imsak", "l'Imsak", "Fin du repas avant l'aube : le jeûne commence."),
    "iftar": ("🌙 Rupture du jeûne", "la rupture du jeûne",
              "Il est l'heure de rompre le jeûne. اللهم لك صمت وعلى رزقك أفطرت"),
}


def build_ramadan_payload(kind: str, minutes: int = 0) -> dict:
    """Notification de rappel Imsak / rupture du jeûne (Ramadan), sans Adhan."""
    title, label, at_time = RAMADAN_KINDS[kind]
    body = f"{label.capitalize()} dans {minutes} minutes." if minutes else at_time
    return {
        "title": title,
        "body": body,
        "tag": f"ramadan-{kind}",
        "data": {"ramadan": kind, "sound_url": None, "alert_mode": "beep",
                 "volume": 100, "fade_in": False},
    }
