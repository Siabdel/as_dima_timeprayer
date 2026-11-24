"""Modèle de lieu pour l'utilisateur (lieu par défaut des horaires)."""
from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _


class Location(models.Model):
    """Un lieu enregistré par l'utilisateur (coordonnées + ville optionnelle)."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="locations",
        verbose_name=_("utilisateur"),
    )
    label = models.CharField(_("libellé"), max_length=120)
    latitude = models.DecimalField(
        _("latitude"), max_digits=9, decimal_places=6,
        validators=[MinValueValidator(-90), MaxValueValidator(90)],
    )
    longitude = models.DecimalField(
        _("longitude"), max_digits=9, decimal_places=6,
        validators=[MinValueValidator(-180), MaxValueValidator(180)],
    )
    city = models.CharField(_("ville"), max_length=120, blank=True)
    country = models.CharField(_("pays"), max_length=120, blank=True)
    timezone = models.CharField(_("fuseau horaire"), max_length=64, blank=True)
    is_default = models.BooleanField(_("lieu par défaut"), default=False)
    created_at = models.DateTimeField(_("créé le"), auto_now_add=True)

    class Meta:
        verbose_name = _("lieu")
        verbose_name_plural = _("lieux")
        ordering = ["-is_default", "created_at"]

    def __str__(self) -> str:
        return self.label or f"{self.latitude}, {self.longitude}"
