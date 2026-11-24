"""Modèles de l'app quran (progression de lecture)."""
from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _


class ReadingProgress(models.Model):
    """
    Progression de lecture du Coran : dernier verset consulté.

    Un enregistrement par utilisateur (le reprendre où on l'a laissé).
    """

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="reading_progress",
        verbose_name=_("utilisateur"),
    )
    last_surah_number = models.PositiveIntegerField(
        _("dernière sourate"), null=True, blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(114)],
    )
    last_ayah_number = models.PositiveIntegerField(
        _("dernier verset"), null=True, blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(286)],
    )
    updated_at = models.DateTimeField(_("mis à jour le"), auto_now=True)
    created_at = models.DateTimeField(_("créé le"), auto_now_add=True)

    class Meta:
        verbose_name = _("progression de lecture")
        verbose_name_plural = _("progressions de lecture")

    def __str__(self) -> str:
        return f"{self.user.email} — sourate {self.last_surah_number}, verset {self.last_ayah_number}"
