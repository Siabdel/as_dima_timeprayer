"""
Serializers de l'application accounts :
- RegisterSerializer : inscription (e-mail + mot de passe confirmé)
- UserSerializer : profil courant (GET/PATCH /auth/me/)
- UserPreferenceSerializer : préférences (GET/PUT /auth/preferences/)
"""
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from .models import User, UserPreference


class RegisterSerializer(serializers.Serializer):
    """Inscription d'un nouvel utilisateur."""

    email = serializers.EmailField()
    password = serializers.CharField(
        write_only=True, validators=[validate_password], style={"input_type": "password"}
    )
    password2 = serializers.CharField(write_only=True, style={"input_type": "password"})
    first_name = serializers.CharField(required=False, allow_blank=True, max_length=150)
    last_name = serializers.CharField(required=False, allow_blank=True, max_length=150)

    def validate_email(self, value: str) -> str:
        email = value.strip().lower()
        if User.objects.filter(email=email).exists():
            raise serializers.ValidationError(
                "Un compte avec cette adresse e-mail existe déjà."
            )
        return email

    def validate(self, attrs):
        if attrs["password"] != attrs["password2"]:
            raise serializers.ValidationError(
                {"password2": "Les mots de passe ne correspondent pas."}
            )
        return attrs

    def create(self, validated_data):
        validated_data.pop("password2")
        return User.objects.create_user(**validated_data)


class UserSerializer(serializers.ModelSerializer):
    """Profil de l'utilisateur authentifié."""

    class Meta:
        model = User
        fields = ["id", "email", "first_name", "last_name"]
        read_only_fields = ["id", "email"]


class UserPreferenceSerializer(serializers.ModelSerializer):
    """Préférences de notification et de calcul des horaires."""

    def validate_adhan_sound_id(self, value: str | None) -> str | None:
        """L'identifiant doit exister dans le catalogue des sons d'Adhan."""
        from apps.notifications import adhan_sounds

        if value and adhan_sounds.get_sound(value) is None:
            raise serializers.ValidationError(
                "Son d'Adhan inconnu : choisissez un son de la liste proposée."
            )
        return value

    ALERT_MODES = ("full", "beep", "vibrate", "silent")
    PRAYER_KEYS = ("fajr", "sunrise", "dhuhr", "asr", "maghrib", "isha")
    REMINDER_CHOICES = (0, 5, 10, 15, 30)

    def validate_fajr_adhan_sound_id(self, value):
        return self.validate_adhan_sound_id(value)

    def validate_timezone(self, value: str) -> str:
        """Vide, ou nom IANA connu (la gestion heure d'été/hiver vient de la base tz)."""
        from zoneinfo import ZoneInfo

        if not value:
            return value
        try:
            ZoneInfo(value)
        except Exception:
            raise serializers.ValidationError("Fuseau horaire inconnu (ex. Europe/Paris).")
        return value

    def validate_alert_modes(self, value):
        if not isinstance(value, dict):
            raise serializers.ValidationError("Format invalide.")
        for prayer, mode in value.items():
            if prayer not in self.PRAYER_KEYS or mode not in self.ALERT_MODES:
                raise serializers.ValidationError(
                    f"Mode d'alerte invalide : {prayer}={mode}."
                )
        return value

    def validate_reminder_minutes_before(self, value: int) -> int:
        if value not in self.REMINDER_CHOICES:
            raise serializers.ValidationError("Choisissez 0, 5, 10, 15 ou 30 minutes.")
        return value

    def validate_ramadan_reminder_minutes(self, value: int) -> int:
        if value not in self.REMINDER_CHOICES:
            raise serializers.ValidationError("Choisissez 0, 5, 10, 15 ou 30 minutes.")
        return value

    class Meta:
        model = UserPreference
        fields = [
            "id",
            "notifications_enabled",
            "fajr",
            "sunrise",
            "dhuhr",
            "asr",
            "maghrib",
            "isha",
            "quiet_hours_start",
            "quiet_hours_end",
            "calculation_method",
            "madhhab",
            "adhan_sound_id",
            "timezone_mode",
            "timezone",
            "language",
            "alert_modes",
            "reminder_minutes_before",
            "ramadan_imsak_reminder",
            "ramadan_iftar_reminder",
            "ramadan_reminder_minutes",
            "fajr_adhan_sound_id",
            "adhan_volume",
            "adhan_fade_in",
            "default_location",
        ]
        read_only_fields = ["id"]
