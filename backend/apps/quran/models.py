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


class Surah(models.Model):
    """Une sourate (copie locale des métadonnées Quran.com)."""

    number = models.PositiveSmallIntegerField(
        _("numéro"), primary_key=True,
        validators=[MinValueValidator(1), MaxValueValidator(114)],
    )
    name_arabic = models.CharField(_("nom arabe"), max_length=60)
    name_transliterated = models.CharField(_("translittération"), max_length=60)
    verses_count = models.PositiveSmallIntegerField(_("nombre de versets"))
    revelation_place = models.CharField(_("lieu de révélation"), max_length=20, blank=True)

    class Meta:
        ordering = ["number"]
        verbose_name = _("sourate")
        verbose_name_plural = _("sourates")

    def __str__(self) -> str:
        return f"{self.number}. {self.name_transliterated}"


class Verse(models.Model):
    """Un verset : texte arabe Uthmani (copie locale)."""

    surah = models.ForeignKey(Surah, on_delete=models.CASCADE, related_name="verses")
    ayah_number = models.PositiveSmallIntegerField(_("numéro du verset"))
    text_uthmani = models.TextField(_("texte Uthmani"))

    class Meta:
        ordering = ["surah_id", "ayah_number"]
        constraints = [
            models.UniqueConstraint(fields=["surah", "ayah_number"], name="uniq_verse_per_surah"),
        ]
        verbose_name = _("verset")
        verbose_name_plural = _("versets")

    def __str__(self) -> str:
        return f"{self.surah_id}:{self.ayah_number}"


class VerseTranslation(models.Model):
    """Traduction d'un verset dans une langue (« fr », « en »)."""

    verse = models.ForeignKey(Verse, on_delete=models.CASCADE, related_name="translations")
    code = models.CharField(_("code langue"), max_length=8)
    resource_id = models.PositiveIntegerField(
        _("ressource Quran.com"), help_text=_("Identifiant de la traduction source (ex. 31 = Hamidullah)."),
    )
    text = models.TextField(_("texte"))

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["verse", "code"], name="uniq_translation_per_verse_lang"),
        ]
        indexes = [models.Index(fields=["code"])]
        verbose_name = _("traduction de verset")
        verbose_name_plural = _("traductions de versets")

    def __str__(self) -> str:
        return f"{self.verse_id} [{self.code}]"
