"""
Vues de l'app events :
- GET /api/v1/events/            → fêtes d'une année grégorienne (public)
- GET /api/v1/events/upcoming/   → prochaines fêtes à partir d'aujourd'hui (public)
- GET /api/v1/events/hijri-year/ → fêtes islamiques d'une année hégirienne (public)
"""
from datetime import date

from rest_framework import permissions, serializers
from rest_framework.response import Response
from rest_framework.views import APIView

from . import services


class HijriDateSerializer(serializers.Serializer):
    """Bloc date hégirienne d'une fête islamique."""

    day = serializers.IntegerField()
    month = serializers.IntegerField()
    year = serializers.IntegerField()
    month_name = serializers.CharField()
    month_name_ar = serializers.CharField()


class EventSerializer(serializers.Serializer):
    """Fête du calendrier (islamique ou marocaine)."""

    id = serializers.CharField()
    name = serializers.CharField()
    name_ar = serializers.CharField()
    type = serializers.ChoiceField(choices=["islamic", "national"])
    date = serializers.DateField()
    hijri_date = HijriDateSerializer(allow_null=True)
    description = serializers.CharField()
    days_until = serializers.IntegerField(required=False)


class EventsView(APIView):
    """Fêtes d'une année grégorienne (défaut : année courante)."""

    permission_classes = [permissions.AllowAny]

    def get(self, request):
        try:
            year = int(request.query_params.get("year", date.today().year))
        except (TypeError, ValueError):
            year = date.today().year
        if not 1900 <= year <= 2100:
            return Response(
                {
                    "error": {
                        "code": "invalid_params",
                        "message": "L'année doit être comprise entre 1900 et 2100.",
                    }
                },
                status=400,
            )
        events = services.get_year_events(year)
        return Response(
            {
                "year": year,
                "hijri_years": sorted(
                    {e["hijri_date"]["year"] for e in events if e["hijri_date"]}
                ),
                "count": len(events),
                "events": EventSerializer(events, many=True).data,
            }
        )


class UpcomingEventsView(APIView):
    """Prochaines fêtes à partir d'aujourd'hui (2 ans glissants au maximum)."""

    permission_classes = [permissions.AllowAny]

    def get(self, request):
        try:
            limit = int(request.query_params.get("limit", 12))
        except (TypeError, ValueError):
            limit = 12
        limit = max(1, min(limit, 50))
        events = services.get_upcoming_events(limit=limit)
        return Response(
            {
                "today": date.today().isoformat(),
                "count": len(events),
                "events": EventSerializer(events, many=True).data,
            }
        )


class HijriYearEventsView(APIView):
    """Fêtes islamiques d'une année hégirienne complète."""

    permission_classes = [permissions.AllowAny]

    def get(self, request):
        try:
            year = int(request.query_params.get("year", 0))
        except (TypeError, ValueError):
            year = 0
        if not year:
            # Défaut : année hégirienne courante.
            year = _current_hijri_year(date.today())
        if not 1400 <= year <= 1500:
            return Response(
                {
                    "error": {
                        "code": "invalid_params",
                        "message": "L'année hégirienne doit être comprise entre 1400 et 1500.",
                    }
                },
                status=400,
            )
        events = services.get_hijri_year_events(year)
        return Response(
            {
                "hijri_year": year,
                "count": len(events),
                "events": EventSerializer(events, many=True).data,
            }
        )


def _current_hijri_year(today: date) -> int:
    """Année hégirienne courante (via hijridate, hors-ligne)."""
    from hijridate import Gregorian

    return Gregorian(today.year, today.month, today.day).to_hijri().year
