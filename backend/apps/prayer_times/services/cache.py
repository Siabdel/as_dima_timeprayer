"""
Cache Redis pour les horaires de prière.

Stratégie :
  * clé principale `prayer:{lat_rounded}:{lng_rounded}:{date}:{method}:{madhhab}`
    (ou un slug ville/pays) avec un TTL jusqu'à la fin de la journée concernée ;
  * clé de secours `prayer-stale:{...}` avec un TTL long (48 h) permettant le
    "stale-while-revalidate" : si Aladhan est indisponible, on sert les données
    périmées avec un drapeau `stale: true`.
"""
from datetime import datetime, timedelta, time
from zoneinfo import ZoneInfo

from django.core.cache import cache

STALE_KEY_PREFIX = "prayer-stale"
STALE_TTL = timedelta(hours=48)


def _round(value: float) -> str:
    """Arrondit une coordonnée à 2 décimales (~1 km : précision suffisante)."""
    return f"{round(float(value), 2):.2f}"


def build_cache_key(*, latitude=None, longitude=None, city=None, country=None,
                    date_iso: str, method: int, madhhab: str) -> str:
    """Clé de cache : coordonnées arrondies ou slug ville/pays."""
    if city:
        location = f"{str(city).strip().lower().replace(' ', '-')}" \
                   f":{str(country or '').strip().lower().replace(' ', '-')}"
    else:
        location = f"{_round(latitude)}:{_round(longitude)}"
    return f"prayer:{location}:{date_iso}:{method}:{madhhab}"


def compute_cache_ttl(date_iso: str, timezone_name: str | None) -> int:
    """
    TTL du cache : jusqu'à la fin de la journée concernée (dans la timezone du
    lieu) si la date est "aujourd'hui", sinon 24 h par défaut.
    """
    try:
        target_date = datetime.strptime(date_iso, "%Y-%m-%d").date()
    except ValueError:
        return int(timedelta(hours=24).total_seconds())

    if timezone_name:
        try:
            tz = ZoneInfo(timezone_name)
        except Exception:
            tz = None
    else:
        tz = None

    if tz is not None and target_date == datetime.now(tz).date():
        end_of_day = datetime.combine(target_date, time.max, tzinfo=tz)
        remaining = end_of_day - datetime.now(tz)
        return max(int(remaining.total_seconds()), 1)

    return int(timedelta(hours=24).total_seconds())


def get_cached(key: str) -> dict | None:
    """Retourne les horaires en cache (clé principale), ou None."""
    return cache.get(key)


def store(key: str, data: dict, ttl_seconds: int) -> None:
    """
    Stocke les horaires : TTL court (fin de journée) sur la clé principale,
    TTL long sur la clé de secours pour le stale-while-revalidate.
    """
    cache.set(key, data, timeout=ttl_seconds)
    cache.set(f"{STALE_KEY_PREFIX}:{key.removeprefix('prayer:')}", data,
              timeout=int(STALE_TTL.total_seconds()))


def get_stale(key: str) -> dict | None:
    """Retourne la sauvegarde périmée (48 h), ou None."""
    return cache.get(f"{STALE_KEY_PREFIX}:{key.removeprefix('prayer:')}")
