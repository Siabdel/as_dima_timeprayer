"""
Classes de limitation de débit dédiées.

Les taux sont déclarés dans settings.REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"].
"""
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle


class RegisterRateThrottle(AnonRateThrottle):
    """Anti-abus sur l'inscription : quelques comptes par IP et par heure."""

    scope = "register"


class NotificationTestRateThrottle(UserRateThrottle):
    """Limite les envois de notification de test par utilisateur."""

    scope = "notification_test"
