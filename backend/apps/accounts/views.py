"""
Vues d'authentification et de préférences :
- POST /api/v1/auth/register/     → inscription (throttle dédié)
- POST /api/v1/auth/token/        → obtention des JWT (SimpleJWT)
- POST /api/v1/auth/token/refresh/→ rafraîchissement
- GET/PATCH /api/v1/auth/me/      → profil courant
- GET/PUT /api/v1/auth/preferences/ → préférences utilisateur
"""
from rest_framework import generics, permissions
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.status import HTTP_400_BAD_REQUEST

from config.throttles import RegisterRateThrottle

from .models import UserPreference
from .serializers import RegisterSerializer, UserPreferenceSerializer, UserSerializer


class RegisterView(generics.CreateAPIView):
    """Inscription — publique, limitée en débit (anti-abus)."""

    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]
    throttle_classes = [RegisterRateThrottle]

    def create(self, request, *args, **kwargs):
        """
        Enregistre un nouvel utilisateur.

        Une course entre le check « e-mail existe déjà » et l'INSERT peut
        lever IntegrityError (deux inscriptions concurrentes du même e-mail) :
        on la convertit en 400 au lieu d'un 500.
        """
        try:
            return super().create(request, *args, **kwargs)
        except Exception as exc:
            from django.db import IntegrityError

            if isinstance(exc, IntegrityError) or "accounts_user_email_key" in str(exc):
                raise ValidationError(
                    {"email": "Un compte avec cette adresse e-mail existe déjà."}
                ) from exc
            raise


class MeView(generics.RetrieveUpdateAPIView):
    """Profil de l'utilisateur authentifié (lecture + mise à jour du nom)."""

    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user


class PreferencesView(generics.RetrieveUpdateAPIView):
    """Préférences de l'utilisateur authentifié (créées à la volée)."""

    serializer_class = UserPreferenceSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        obj, _ = UserPreference.objects.get_or_create(user=self.request.user)
        return obj
