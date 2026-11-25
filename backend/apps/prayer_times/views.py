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
from django.core.cache import cache as django_cache

from .services import aladhan, cache as prayer_cache, ramadan as ramadan_service

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


RAMADAN_TTL = 7 * 24 * 3600
RAMADAN_STALE_TTL = 60 * 24 * 3600


def _default_ramadan_year() -> int:
    """Année hégirienne du Ramadan en cours ou du prochain (si le mois 9 est passé)."""
    from hijridate import Gregorian

    today = dj_timezone.now().date()
    h = Gregorian(today.year, today.month, today.day).to_hijri()
    return h.year + 1 if h.month > aladhan.RAMADAN_MONTH else h.year


class RamadanCalendarView(APIView):
    """
    GET /api/v1/prayer-times/ramadan/?hijri_year=1448&latitude=&longitude=&method=&madhhab=

    Horaires de chaque jour de Ramadan (imsak, rupture du jeûne = maghrib…)
    et dates importantes (Nuit du Destin, Aïd…). Coordonnées obligatoires.
    `hijri_year` est facultatif : Ramadan en cours ou prochain.
    """

    permission_classes = [AllowAny]

    def get(self, request):
        params = request.query_params
        try:
            latitude = float(params.get("latitude"))
            longitude = float(params.get("longitude"))
        except (TypeError, ValueError):
            return _error_response(
                "invalid_params", "Fournissez latitude et longitude numériques.",
                status.HTTP_400_BAD_REQUEST,
            )
        if not (-90 <= latitude <= 90) or not (-180 <= longitude <= 180):
            return _error_response("invalid_params", "Coordonnées hors limites.",
                                   status.HTTP_400_BAD_REQUEST)
        madhhab = params.get("madhhab", "standard")
        if madhhab not in VALID_MADHHABS:
            return _error_response(
                "invalid_madhhab",
                f"Le paramètre madhhab doit être l'un de : {', '.join(VALID_MADHHABS)}.",
                status.HTTP_400_BAD_REQUEST,
            )
        try:
            method = int(params.get("method", 3))
            hijri_year = int(params.get("hijri_year") or _default_ramadan_year())
        except ValueError:
            return _error_response(
                "invalid_params", "method et hijri_year doivent être des entiers.",
                status.HTTP_400_BAD_REQUEST,
            )
        if not (1400 <= hijri_year <= 1500):
            return _error_response("invalid_params", "hijri_year hors limites (1400-1500).",
                                   status.HTTP_400_BAD_REQUEST)

        key = (f"ramadan:{hijri_year}:{prayer_cache._round(latitude)}:"
               f"{prayer_cache._round(longitude)}:{method}:{madhhab}")
        stale_key = f"ramadan-stale:{key}"
        data = django_cache.get(key)
        stale = False
        if data is None:
            try:
                data = aladhan.fetch_ramadan_calendar(
                    hijri_year=hijri_year, latitude=latitude, longitude=longitude,
                    method=method, madhhab=madhhab,
                )
                django_cache.set(key, data, RAMADAN_TTL)
                django_cache.set(stale_key, data, RAMADAN_STALE_TTL)
            except aladhan.AladhanError as exc:
                data = django_cache.get(stale_key)
                if data is None:
                    return _error_response(
                        "external_api_error",
                        f"Impossible de récupérer le calendrier de Ramadan : {exc}",
                        status.HTTP_503_SERVICE_UNAVAILABLE,
                    )
                stale = True

        days = data["days"]
        return Response({
            "hijri_year": hijri_year,
            "location": {"latitude": latitude, "longitude": longitude},
            "method": method,
            "madhhab": madhhab,
            "timezone": data.get("timezone", ""),
            "start_date": days[0]["date"],
            "end_date": days[-1]["date"],
            "days_count": len(days),
            "days": days,
            "key_dates": ramadan_service.build_key_dates(days),
            "stale": stale,
        })
