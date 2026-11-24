"""GET /api/v1/weather/ — météo du lieu (public, mis en cache 15 min)."""
from django.core.cache import cache
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from . import client

CACHE_TTL = 15 * 60


def _error(code: str, message: str, http_status: int) -> Response:
    return Response({"error": {"code": code, "message": message}}, status=http_status)


class WeatherView(APIView):
    """Paramètres : latitude+longitude, ou city[+country]."""

    permission_classes = [permissions.AllowAny]

    def get(self, request):
        params = request.query_params
        try:
            if params.get("latitude") is not None and params.get("longitude") is not None:
                latitude = float(params["latitude"])
                longitude = float(params["longitude"])
                name = params.get("city", "")
            elif params.get("city"):
                place = client.geocode(params["city"].strip(), params.get("country", "").strip())
                latitude, longitude, name = place["latitude"], place["longitude"], place["name"]
            else:
                return _error(
                    "invalid_params", "Fournissez latitude+longitude ou city.",
                    status.HTTP_400_BAD_REQUEST,
                )
        except ValueError:
            return _error(
                "invalid_params", "Latitude et longitude doivent être numériques.",
                status.HTTP_400_BAD_REQUEST,
            )
        except client.WeatherError as exc:
            return _error("not_found", str(exc), status.HTTP_404_NOT_FOUND)

        if not (-90 <= latitude <= 90) or not (-180 <= longitude <= 180):
            return _error("invalid_params", "Coordonnées hors limites.", status.HTTP_400_BAD_REQUEST)

        # Cache sur coordonnées arrondies (~1 km) : peu d'appels sortants.
        key = f"weather:{latitude:.2f}:{longitude:.2f}"
        data = cache.get(key)
        if data is None:
            try:
                data = client.fetch_forecast(latitude, longitude)
            except client.WeatherError as exc:
                return _error("external_api_error", str(exc), status.HTTP_503_SERVICE_UNAVAILABLE)
            cache.set(key, data, CACHE_TTL)
        return Response({
            "location": {"name": name, "latitude": latitude, "longitude": longitude},
            **data,
        })
