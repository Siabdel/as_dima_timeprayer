"""Modèles de l'app notifications (abonnements Web Push + journal d'envoi)."""
from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _


class PushSubscription(models.Model):
    """
    Un abonnement Web Push d'un utilisateur (navigateur).

    `endpoint` est unique : un même navigateur ne peut s'abonner qu'une fois.
    Les clés p256dh/auth sont les clés ECDH du navigateur (chiffrées par
    pywebpush, jamais exposées).
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="push_subscriptions",
        verbose_name=_("utilisateur"),
    )
    endpoint = models.URLField(_("endpoint"), max_length=500, unique=True)
    p256dh = models.CharField(_("clé p256dh"), max_length=200)
    auth = models.CharField(_("clé auth"), max_length=200)
    user_agent = models.CharField(_("navigateur"), max_length=300, blank=True)
    created_at = models.DateTimeField(_("créé le"), auto_now_add=True)
    renewed_at = models.DateTimeField(_("renouvelé le"), null=True, blank=True)
    last_error_at = models.DateTimeField(_("dernière erreur"), null=True, blank=True)

    class Meta:
        verbose_name = _("abonnement push")
        verbose_name_plural = _("abonnements push")

    def __str__(self) -> str:
        return f"{self.user.email} — {self.endpoint[:60]}…"


class PrayerNotificationLog(models.Model):
    """
    Journal d'envoi des notifications Adhan.

    La contrainte d'unicité (user, prayer_name, date) garantit l'idempotence :
    une même prière n'est jamais notifiée deux fois à un utilisateur.
    """

    STATUS_SENT = "sent"
    STATUS_SKIPPED_QUIET = "skipped_quiet"
    STATUS_SKIPPED_DISABLED = "skipped_disabled"
    STATUS_SKIPPED_NO_SUB = "skipped_no_subscription"
    STATUS_CHOICES = [
        (STATUS_SENT, "envoyée"),
        (STATUS_SKIPPED_QUIET, "ignorée (heures calmes)"),
        (STATUS_SKIPPED_DISABLED, "ignorée (préférence désactivée)"),
        (STATUS_SKIPPED_NO_SUB, "ignorée (aucun abonnement)"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notification_logs",
        verbose_name=_("utilisateur"),
    )
    prayer_name = models.CharField(_("prière"), max_length=16)
    date = models.DateField(_("date"))
    status = models.CharField(
        _("statut"), max_length=32, choices=STATUS_CHOICES, default=STATUS_SENT
    )
    sent_at = models.DateTimeField(_("envoyée le"), null=True, blank=True)
    created_at = models.DateTimeField(_("créé le"), auto_now_add=True)

    class Meta:
        verbose_name = _("notification")
        verbose_name_plural = _("notifications")
        unique_together = [("user", "prayer_name", "date")]
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.user.email} — {self.prayer_name} — {self.date} — {self.status}"
