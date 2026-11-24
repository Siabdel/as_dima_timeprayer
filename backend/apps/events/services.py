"""
Calcul des fêtes à venir (islamiques + marocaines) pour une année grégorienne.

Les fêtes islamiques sont récurrentes en calendrier hégirien : on énumère les
années hégiriennes qui recouvrent l'année grégorienne demandée (une année
hégirienne est ~354 jours, il faut donc 3 années hégiriennes pour couvrir
une année grégorienne), convertit chaque date hégirienne en grégorien via
`hijridate`, et ne conserve que les dates tombant dans l'année demandée.
"""
from datetime import date

from hijridate import Gregorian, Hijri

from .fetes import ISLAMIC_EVENTS, MOROCCAN_EVENTS


def _hijri_to_gregorian_safe(hijri: Hijri) -> date | None:
    """
    Convertit une date hégirienne en grégorien, ou None si hors plage
    (la bibliothèque couvre environ 1924-2124 grégorien).
    """
    try:
        greg = hijri.to_gregorian()
        return date(greg.year, greg.month, greg.day)
    except (ValueError, OverflowError):
        return None


def _hijri_event_dates(year: int) -> list[dict]:
    """Dates grégoriennes des fêtes islamiques tombant dans l'année `year`."""
    results: list[dict] = []
    # Une année hégirienne (~354 jours) commence vers juillet grégorien :
    # l'année grégorienne `year` chevauche 2 années hégiriennes (par ex.
    # 2026 ≈ 1447-1448 H). On énumère les années hégiriennes couvrant les
    # 1er janvier et 31 décembre grégoriens de l'année demandée.
    hijri_year_jan = Gregorian(year, 1, 1).to_hijri().year
    hijri_year_dec = Gregorian(year, 12, 31).to_hijri().year
    hijri_years = range(hijri_year_jan, hijri_year_dec + 1)
    for event in ISLAMIC_EVENTS:
        seen_dates: set[date] = set()
        for hy in hijri_years:
            hijri = Hijri(hy, event.hijri_month, event.hijri_day)
            greg = _hijri_to_gregorian_safe(hijri)
            if greg is None or greg.year != year:
                continue
            if greg in seen_dates:
                continue
            seen_dates.add(greg)
            results.append(
                {
                    "id": event.id,
                    "name": event.name,
                    "name_ar": event.name_ar,
                    "type": "islamic",
                    "date": greg.isoformat(),
                    "hijri_date": {
                        "day": event.hijri_day,
                        "month": event.hijri_month,
                        "year": hy,
                        "month_name": hijri.month_name("en"),
                        "month_name_ar": hijri.month_name("ar"),
                    },
                    "description": event.description,
                }
            )
    return results


def _national_event_dates(year: int) -> list[dict]:
    """Dates des fêtes nationales marocaines de l'année `year`."""
    results: list[dict] = []
    for event in MOROCCAN_EVENTS:
        results.append(
            {
                "id": event.id,
                "name": event.name,
                "name_ar": event.name_ar,
                "type": "national",
                "date": date(year, event.month, event.day).isoformat(),
                "hijri_date": None,
                "description": event.description,
            }
        )
    return results


def get_year_events(year: int) -> list[dict]:
    """
    Toutes les fêtes (islamiques + marocaines) de l'année grégorienne `year`,
    triées par date croissante.
    """
    events = _hijri_event_dates(year) + _national_event_dates(year)
    events.sort(key=lambda e: e["date"])
    return events


def get_upcoming_events(from_date: date | None = None, limit: int = 12) -> list[dict]:
    """
    Prochaines fêtes à partir de `from_date` (défaut : aujourd'hui),
    sur les deux années grégoriennes à venir, `limit` maximum.
    Chaque entrée porte un champ `days_until` calculé.
    """
    from_date = from_date or date.today()
    events: list[dict] = []
    for year in (from_date.year, from_date.year + 1):
        events.extend(get_year_events(year))
    events.sort(key=lambda e: e["date"])

    upcoming = []
    for event in events:
        event_date = date.fromisoformat(event["date"])
        if event_date < from_date:
            continue
        event["days_until"] = (event_date - from_date).days
        upcoming.append(event)
        if len(upcoming) >= limit:
            break
    return upcoming


def get_hijri_year_events(hijri_year: int) -> list[dict]:
    """
    Toutes les fêtes islamiques d'une année hégirienne (1 Muharram → 30
    Dhu al-Hijjah), triées par mois hégirien. Utile pour afficher le
    calendrier d'une année hégirienne complète.
    """
    results: list[dict] = []
    for event in ISLAMIC_EVENTS:
        hijri = Hijri(hijri_year, event.hijri_month, event.hijri_day)
        greg = _hijri_to_gregorian_safe(hijri)
        if greg is None:
            continue
        results.append(
            {
                "id": event.id,
                "name": event.name,
                "name_ar": event.name_ar,
                "type": "islamic",
                "date": greg.isoformat(),
                "hijri_date": {
                    "day": event.hijri_day,
                    "month": event.hijri_month,
                    "year": hijri_year,
                    "month_name": hijri.month_name("en"),
                    "month_name_ar": hijri.month_name("ar"),
                },
                "description": event.description,
            }
        )
    results.sort(key=lambda e: e["hijri_date"]["month"])
    return results
