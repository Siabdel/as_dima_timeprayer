"""
Vues de l'app notifications :
- GET  /api/v1/notifications/adhan-sounds/ → catalogue des sons d'Adhan (public)
- GET  /api/v1/notifications/vapid-key/    → clé publique VAPID (public)
- POST /api/v1/notifications/subscribe/    → enregistre un abonnement (JWT)
- DELETE /api/v1/notifications/subscribe/  → supprime un abonnement (JWT)
- GET  /api/v1/notifications/status/       → état de l'abonnement (JWT)
- POST /api/v1/notifications/test/         → notification de test (JWT, throttle)
"""
import logging

from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from config.throttles import NotificationTestRateThrottle

from . import adhan_sounds
from .models import PrayerNotificationLog, PushSubscription
from .serializers import PushSubscriptionSerializer, TestNotificationSerializer
from .services.push import build_payload, send_push
from .tasks import send_prayer_notification

logger = logging.getLogger(__name__)


class AdhanSoundsView(APIView):
    """
    Catalogue des sons d'Adhan (public : la donnée est statique et non
    personnelle). Le frontend l'utilise pour afficher le sélecteur dans les
    réglages et précharger l'aperçu audio.
    """

    permission_classes = [permissions.AllowAny]

    def get(self, request):
        return Response(
            {
                "sounds": adhan_sounds.as_list(),
                "default": adhan_sounds.DEFAULT_SOUND_ID,
            }
        )


class VapidKeyView(APIView):
    """Clé publique VAPID — nécessaire au navigateur pour s'abonner."""

    permission_classes = [permissions.AllowAny]

    def get(self, request):
        return Response({"public_key": settings_vapid_public_key()})


def settings_vapid_public_key() -> str:
    from django.conf import settings

    return settings.VAPID_PUBLIC_KEY


class SubscribeView(APIView):
    """Enregistre (ou renouvelle) l'abonnement Web Push de l'utilisateur."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = PushSubscriptionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        subscription, created = PushSubscription.objects.update_or_create(
            endpoint=data["endpoint"],
            defaults={
                "user": request.user,
                "p256dh": data["keys"]["p256dh"],
                "auth": data["keys"]["auth"],
                "user_agent": data.get("user_agent", "") or request.META.get("HTTP_USER_AGENT", "")[:300],
                "renewed_at": None,
                "last_error_at": None,
            },
        )
        if created:
            subscription.renewed_at = subscription.created_at
            subscription.save(update_fields=["renewed_at"])

        return Response(
            {"status": "subscribed", "endpoint": subscription.endpoint},
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )

    def delete(self, request):
        """Désabonnement : l'endpoint est passé dans le corps."""
        endpoint = request.data.get("endpoint")
        if not endpoint:
            return Response(
                {"error": {"code": "invalid_params", "message": "Le champ endpoint est requis."}},
                status=status.HTTP_400_BAD_REQUEST,
            )
        deleted, _ = PushSubscription.objects.filter(
            user=request.user, endpoint=endpoint
        ).delete()
        return Response({"status": "unsubscribed", "deleted": deleted})


class SubscriptionStatusView(APIView):
    """État de l'abonnement push et des dernières notifications."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        subscriptions = PushSubscription.objects.filter(user=request.user)
        logs = PrayerNotificationLog.objects.filter(user=request.user)[:10]
        return Response(
            {
                "subscribed": subscriptions.exists(),
                "subscriptions_count": subscriptions.count(),
                "recent_notifications": [
                    {
                        "prayer": log.prayer_name,
                        "date": log.date,
                        "status": log.status,
                        "sent_at": log.sent_at,
                    }
                    for log in logs
                ],
            }
        )


class TestNotificationView(APIView):
    """Envoie une notification de test (limitée en débit)."""

    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [NotificationTestRateThrottle]

    def post(self, request):
        serializer = TestNotificationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        prayer_name = serializer.validated_data["prayer_name"]

        subscriptions = PushSubscription.objects.filter(user=request.user)
        if not subscriptions.exists():
            return Response(
                {"error": {"code": "no_subscription", "message": "Aucun abonnement push enregistré."}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # La notification de test joue le son choisi par l'utilisateur
        # (identique au comportement d'une vraie notification Adhan).
        prefs = getattr(request.user, "preferences", None)
        sound_url = adhan_sounds.get_sound_url(getattr(prefs, "adhan_sound_id", None))
        payload = build_payload(prayer_name, sound_url=sound_url)
        payload["title"] = "🔔 Notification de test"
        payload["body"] = f"Configuration OK — vous recevrez les rappels du {prayer_name}."

        sent, gone = 0, 0
        for subscription in subscriptions:
            try:
                send_push(subscription, payload)
                sent += 1
            except Exception as exc:  # noqa: BLE001 — vue : on journalise et on continue
                logger.warning("Test push échoué pour %s : %s", request.user.id, exc)
                from .services.push import GoneSubscriptionError

                if isinstance(exc, GoneSubscriptionError):
                    subscription.delete()
                    gone += 1

        if sent == 0:
            return Response(
                {"error": {"code": "push_failed", "message": "L'envoi de la notification a échoué."}},
                status=status.HTTP_502_BAD_GATEWAY,
            )
        return Response({"status": "sent", "sent": sent, "removed": gone})
