"""
Vues des horaires de prière :
- GET /api/v1/prayer-times/          → public (lat/lng ou city/country)
- GET /api/v1/prayer-times/today/    → JWT requis (lieu par défaut de l'utilisateur)

Règle de cache : ne jamais appeler Aladhan pour une requête déjà en cache.
Si Aladhan échoue et qu'une entrée périmée existe, la servir avec stale:true.
"""
import logging
from datetime import datetime

from django.utils import timezone as dj_timezone
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.models import UserPreference

from .serializers import PrayerTimesSerializer
from .services import aladhan, cache as prayer_cache

logger = logging.getLogger(__name__)

VALID_MADHHABS = ("standard", "hanafi")
DATE_FORMAT = "%Y-%m-%d"


def _error_response(code: str, message: str, http_status: int) -> Response:
    """Format d'erreur uniforme {"error": {code, message}}."""
    return Response({"error": {"code": code, "message": message}}, status=http_status)


def _parse_date(value: str | None) -> str | None:
    """Valide le paramètre date (YYYY-MM-DD), retourne None si invalide."""
    if not value:
        return None
    try:
        datetime.strptime(value, DATE_FORMAT)
    except ValueError:
        return None
    return value


def _get_prayer_times(*, latitude, longitude, city, country, date_iso,
                      method, madhhab) -> tuple[dict, bool]:
    """
    Récupère les horaires : cache d'abord, puis Aladhan, puis stale.
    Retourne (données, stale).
    """
    key = prayer_cache.build_cache_key(
        latitude=latitude, longitude=longitude, city=city, country=country,
        date_iso=date_iso, method=method, madhhab=madhhab,
    )

    # 1. Cache : aucune requête externe si la donnée est fraîche.
    cached = prayer_cache.get_cached(key)
    if cached is not None:
        return cached, False

    # 2. Aladhan ; en cas d'échec → 3. sauvegarde périmée (stale-while-revalidate).
    try:
        data = aladhan.fetch_prayer_times(
            date_iso=date_iso,
            latitude=latitude, longitude=longitude,
            city=city, country=country,
            method=method, madhhab=madhhab,
        )
        ttl = prayer_cache.compute_cache_ttl(date_iso, data.get("timezone"))
        prayer_cache.store(key, data, ttl)
        return data, False
    except aladhan.AladhanError:
        logger.warning("Aladhan indisponible pour %s — tentative de lecture stale", key)
        stale = prayer_cache.get_stale(key)
        if stale is not None:
            return stale, True
        raise


class PrayerTimesView(APIView):
    """Horaires de prière — accessibles sans authentification."""

    permission_classes = [AllowAny]

    def get(self, request):
        params = request.query_params

        latitude = params.get("latitude")
        longitude = params.get("longitude")
        city = params.get("city")
        country = params.get("country")
        date_iso = _parse_date(params.get("date")) or dj_timezone.now().strftime(DATE_FORMAT)
        madhhab = params.get("madhhab", "standard")

        if date_iso != params.get("date") and params.get("date"):
            return _error_response(
                "invalid_date", "Le paramètre date doit être au format YYYY-MM-DD.",
                status.HTTP_400_BAD_REQUEST,
            )

        if madhhab not in VALID_MADHHABS:
            return _error_response(
                "invalid_madhhab",
                f"Le paramètre madhhab doit être l'un de : {', '.join(VALID_MADHHABS)}.",
                status.HTTP_400_BAD_REQUEST,
            )

        try:
            method = int(params.get("method", 3))
        except ValueError:
            return _error_response(
                "invalid_method", "Le paramètre method doit être un entier.",
                status.HTTP_400_BAD_REQUEST,
            )

        has_coords = latitude is not None and longitude is not None
        has_city = bool(city)
        if not has_coords and not has_city:
            return _error_response(
                "invalid_params",
                "Fournissez soit latitude+longitude, soit city+country.",
                status.HTTP_400_BAD_REQUEST,
            )

        if has_coords:
            try:
                latitude = float(latitude)
                longitude = float(longitude)
            except ValueError:
                return _error_response(
                    "invalid_params", "Latitude et longitude doivent être numériques.",
                    status.HTTP_400_BAD_REQUEST,
                )
            if not (-90 <= latitude <= 90) or not (-180 <= longitude <= 180):
                return _error_response(
                    "invalid_params", "Coordonnées hors limites.",
                    status.HTTP_400_BAD_REQUEST,
                )
            location = {"latitude": latitude, "longitude": longitude}
        else:
            location = {"city": city, "country": country or ""}

        try:
            data, stale = _get_prayer_times(
                latitude=latitude, longitude=longitude, city=city, country=country,
                date_iso=date_iso, method=method, madhhab=madhhab,
            )
        except aladhan.AladhanError as exc:
            return _error_response(
                "external_api_error",
                f"Impossible de récupérer les horaires : {exc}",
                status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        payload = {
            **data,
            "location": location,
            "date": date_iso,
            "method": method,
            "madhhab": madhhab,
            "stale": stale,
        }
        response = Response(PrayerTimesSerializer(payload).data)
        if stale:
            # RFC 7231 : avertissement standard "réponse périmée".
            response["Warning"] = '110 - "Response is stale"'
        return response


class PrayerTimesTodayView(APIView):
    """Horaires du jour pour le lieu par défaut de l'utilisateur (JWT requis)."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            prefs = UserPreference.objects.get(user=request.user)
        except UserPreference.DoesNotExist:
            prefs = None

        location = prefs.default_location if prefs else None
        if location is None:
            return _error_response(
                "no_default_location",
                "Aucun lieu par défaut défini. Enregistrez d'abord un lieu.",
                status.HTTP_400_BAD_REQUEST,
            )

        method = prefs.calculation_method if prefs and prefs.calculation_method is not None else 3
        madhhab = prefs.madhhab if prefs else "standard"
        date_iso = dj_timezone.now().strftime(DATE_FORMAT)

        try:
            data, stale = _get_prayer_times(
                latitude=float(location.latitude), longitude=float(location.longitude),
                city=None, country=None,
                date_iso=date_iso, method=method, madhhab=madhhab,
            )
        except aladhan.AladhanError as exc:
            return _error_response(
                "external_api_error",
                f"Impossible de récupérer les horaires : {exc}",
                status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        payload = {
            **data,
            "location": {
                "latitude": float(location.latitude),
                "longitude": float(location.longitude),
                "label": location.label,
            },
            "date": date_iso,
            "method": method,
            "madhhab": madhhab,
            "stale": stale,
        }
        response = Response(PrayerTimesSerializer(payload).data)
        if stale:
            response["Warning"] = '110 - "Response is stale"'
        return response
