"""
Modèles de l'app library : cahier de douâas et hadiths du Prophète ﷺ.

Contenu : catalogue statique, chargé par la commande de gestion
`python manage.py seed_library` (module apps.library.content). Le contenu
est authentique (sources citées : Bukhârî, Muslim, Abû Dâwûd, Tirmidhî) et
livré avec texte arabe, translittération (douâas) et traduction française.
"""
from django.db import models
from django.utils.translation import gettext_lazy as _


class Dua(models.Model):
    """Douâa (invocation) avec sa source authentique."""

    CATEGORY_CHOICES = [
        ("reveil", _("Réveil & sommeil")),
        ("repas", _("Repas")),
        ("maison", _("Maison")),
        ("mosquee", _("Mosquée")),
        ("protection", _("Protection")),
        ("pardon", _("Pardon & repentir")),
        ("vie", _("Vie quotidienne")),
    ]

    category = models.CharField(_("catégorie"), max_length=16, choices=CATEGORY_CHOICES)
    title = models.CharField(_("titre"), max_length=120)
    text_ar = models.TextField(_("texte arabe"))
    transliteration = models.TextField(_("translittération"), blank=True)
    translation_fr = models.TextField(_("traduction française"))
    source = models.CharField(_("source"), max_length=120, help_text=_("ex. Sahîh al-Bukhârî 6312"))
    order = models.PositiveIntegerField(_("ordre d'affichage"), default=0)

    class Meta:
        verbose_name = _("douâa")
        verbose_name_plural = _("douâas")
        ordering = ["category", "order"]

    def __str__(self) -> str:
        return f"{self.title} ({self.category})"


class Hadith(models.Model):
    """Hadith du Prophète ﷺ avec sa source."""

    CATEGORY_CHOICES = [
        ("foi", _("Foi & intentions")),
        ("priere", _("Prière & culte")),
        ("morale", _("Morale & comportement")),
        ("bienfaisance", _("Bienfaisance")),
        ("relations", _("Relations & famille")),
    ]

    category = models.CharField(_("catégorie"), max_length=16, choices=CATEGORY_CHOICES)
    title = models.CharField(_("titre"), max_length=120)
    text_ar = models.TextField(_("texte arabe"))
    translation_fr = models.TextField(_("traduction française"))
    narrator = models.CharField(_("narrateur"), max_length=80, help_text=_("ex. 'Umar ibn al-Khattâb"))
    source = models.CharField(_("source"), max_length=120, help_text=_("ex. Sahîh al-Bukhârî 1"))
    order = models.PositiveIntegerField(_("ordre d'affichage"), default=0)

    class Meta:
        verbose_name = _("hadith")
        verbose_name_plural = _("hadiths")
        ordering = ["category", "order"]

    def __str__(self) -> str:
        return f"{self.title} ({self.source})"
