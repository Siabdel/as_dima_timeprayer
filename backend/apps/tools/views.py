"""
Vues de l'app tools :
- GET /api/v1/qibla/?lat=&lng=   → cap vers La Mecque (grand cercle)
- GET /api/v1/hijri/?date=YYYY-MM-DD → conversion grégorien -> hégirien
"""
from datetime import date as date_cls, datetime

from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .services import hijri as hijri_service
from .services import qibla as qibla_service


def _error_response(code: str, message: str, http_status: int) -> Response:
    return Response({"error": {"code": code, "message": message}}, status=http_status)


class QiblaView(APIView):
    """Cap vers La Mecque — public, calcul local (aucun appel externe)."""

    permission_classes = [AllowAny]

    def get(self, request):
        lat = request.query_params.get("lat")
        lng = request.query_params.get("lng")
        if lat is None or lng is None:
            return _error_response(
                "invalid_params", "Fournissez les paramètres lat et lng.",
                status.HTTP_400_BAD_REQUEST,
            )
        try:
            lat, lng = float(lat), float(lng)
        except ValueError:
            return _error_response(
                "invalid_params", "lat et lng doivent être numériques.",
                status.HTTP_400_BAD_REQUEST,
            )
        if not -90 <= lat <= 90 or not -180 <= lng <= 180:
            return _error_response(
                "invalid_params", "Coordonnées hors limites.",
                status.HTTP_400_BAD_REQUEST,
            )

        direction = qibla_service.qibla_direction(lat, lng)
        distance = qibla_service.kaaba_distance_km(lat, lng)
        return Response({
            "qibla_direction": round(direction, 1),
            "compass_point": qibla_service.compass_point(direction),
            "kaaba_distance_km": round(distance, 1),
        })


class HijriView(APIView):
    """Conversion grégorien -> hégirien (Umm al-Qura via hijridate)."""

    permission_classes = [AllowAny]

    def get(self, request):
        date_param = request.query_params.get("date")
        if not date_param:
            # Défaut : aujourd'hui (UTC)
            target = date_cls.today()
        else:
            try:
                target = datetime.strptime(date_param, "%Y-%m-%d").date()
            except ValueError:
                return _error_response(
                    "invalid_date", "Le paramètre date doit être au format YYYY-MM-DD.",
                    status.HTTP_400_BAD_REQUEST,
                )

        hijri = hijri_service.gregorian_to_hijri(target)
        return Response({
            "gregorian_date": target.strftime("%Y-%m-%d"),
            "hijri_date": hijri,
        })
