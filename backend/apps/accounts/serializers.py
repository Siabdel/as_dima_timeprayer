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
            "default_location",
        ]
        read_only_fields = ["id"]
