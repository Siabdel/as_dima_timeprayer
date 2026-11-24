"""Serializers de l'app notifications."""
from rest_framework import serializers

from .models import PushSubscription


class PushSubscriptionSerializer(serializers.ModelSerializer):
    """Corps attendu par POST /notifications/subscribe/."""

    keys = serializers.DictField(
        child=serializers.CharField(),
        help_text='{"p256dh": "...", "auth": "..."}',
    )

    class Meta:
        model = PushSubscription
        fields = ["endpoint", "keys", "user_agent"]
        extra_kwargs = {
            # Pas de UniqueValidator : la vue gère l'upsert (renouvellement
            # d'un abonnement existant par le même endpoint).
            "endpoint": {"validators": []},
            "user_agent": {"required": False, "allow_blank": True},
        }

    def validate_keys(self, value: dict) -> dict:
        p256dh = value.get("p256dh")
        auth = value.get("auth")
        if not p256dh or not auth:
            raise serializers.ValidationError(
                "Les clés p256dh et auth sont obligatoires."
            )
        return value

    def validate_endpoint(self, value: str) -> str:
        if not value.startswith(("https://", "http://")):
            raise serializers.ValidationError("Endpoint invalide.")
        return value


class SubscribeResponseSerializer(serializers.Serializer):
    """Réponse après un abonnement réussi."""

    status = serializers.CharField()
    endpoint = serializers.CharField()


class TestNotificationSerializer(serializers.Serializer):
    """Paramètres optionnels de la notification de test."""

    prayer_name = serializers.ChoiceField(
        choices=["fajr", "sunrise", "dhuhr", "asr", "maghrib", "isha"],
        default="dhuhr",
    )
