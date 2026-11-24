"""
Modèles du compte utilisateur.

Choix de conception : l'e-mail est l'identifiant unique (USERNAME_FIELD),
aucun pseudo n'est requis. Les préférences (rappels par prière, heures
calmes, méthode de calcul) vivent dans UserPreference.
"""
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _


class UserManager(BaseUserManager):
    """Gestionnaire sans pseudo : l'e-mail sert d'identifiant."""

    use_in_migrations = True

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("L'adresse e-mail est obligatoire.")
        email = self.normalize_email(email).lower()
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        if extra_fields.get("is_staff") is not True:
            raise ValueError("Un superutilisateur doit avoir is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Un superutilisateur doit avoir is_superuser=True.")
        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    """Utilisateur identifié par e-mail (pas de pseudo)."""

    username = None  # suppression du champ pseudo hérité d'AbstractUser
    email = models.EmailField(_("adresse e-mail"), unique=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = UserManager()

    class Meta:
        verbose_name = _("utilisateur")
        verbose_name_plural = _("utilisateurs")

    def __str__(self) -> str:
        return self.email


class UserPreference(models.Model):
    """
    Préférences de l'utilisateur : rappels Adhan par prière, heures calmes,
    méthode de calcul et madhhab par défaut (utilisées par /prayer-times/today/).
    """

    MADHHAB_CHOICES = [
        ("standard", "Standard (Chaafi, Hanbali, Maliki)"),
        ("hanafi", "Hanafi"),
    ]

    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="preferences", verbose_name=_("utilisateur")
    )

    # Notifications Adhan
    notifications_enabled = models.BooleanField(
        _("notifications activées"), default=False
    )
    fajr = models.BooleanField(_("rappel Fajr"), default=True)
    sunrise = models.BooleanField(_("rappel Sunrise"), default=False)
    dhuhr = models.BooleanField(_("rappel Dhuhr"), default=True)
    asr = models.BooleanField(_("rappel Asr"), default=True)
    maghrib = models.BooleanField(_("rappel Maghrib"), default=True)
    isha = models.BooleanField(_("rappel Isha"), default=True)
    # Heures calmes : aucune notification entre start et end (fenêtre pouvant
    # traverser minuit, ex. 22:00 -> 06:00).
    quiet_hours_start = models.TimeField(_("début heures calmes"), null=True, blank=True)
    quiet_hours_end = models.TimeField(_("fin heures calmes"), null=True, blank=True)

    # Préférences de calcul des horaires
    calculation_method = models.PositiveIntegerField(
        _("méthode de calcul"), null=True, blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(30)],
        help_text=_("Identifiant de méthode Aladhan (ex. 2 = ISNA, 3 = MWL)."),
    )
    madhhab = models.CharField(
        _("madhhab"), max_length=16, choices=MADHHAB_CHOICES, default="standard"
    )

    # Son d'Adhan choisi (identifiant du catalogue apps.notifications.adhan_sounds).
    # Null/blank = son par défaut du catalogue. La validation de l'identifiant
    # est faite au niveau du serializer (le catalogue peut évoluer sans migration).
    adhan_sound_id = models.CharField(
        _("son d'Adhan"), max_length=32, null=True, blank=True,
        help_text=_("Identifiant du son d'Adhan choisi (voir le catalogue des sons)."),
    )

    # Lieu par défaut utilisé par /prayer-times/today/
    default_location = models.ForeignKey(
        "locations.Location",
        verbose_name=_("lieu par défaut"),
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )

    class Meta:
        verbose_name = _("préférence utilisateur")
        verbose_name_plural = _("préférences utilisateur")

    def __str__(self) -> str:
        return f"Préférences de {self.user.email}"

    def is_prayer_enabled(self, prayer_name: str) -> bool:
        """Rappel activé pour cette prière ? (préférence + global)."""
        if not self.notifications_enabled:
            return False
        return bool(getattr(self, prayer_name, False))
