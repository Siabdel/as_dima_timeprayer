"""
Client Open-Meteo (météo + géocodage), API publique sans clé.

Appels faits côté serveur : le navigateur ne contacte jamais Open-Meteo.
"""
import requests
from django.conf import settings

FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
REQUEST_TIMEOUT = 10

# Libellés français des codes météo WMO.
WMO_LABELS = {
    0: "Ensoleillé", 1: "Plutôt dégagé", 2: "Partiellement nuageux", 3: "Couvert",
    45: "Brouillard", 48: "Brouillard givrant",
    51: "Bruine légère", 53: "Bruine", 55: "Bruine dense",
    56: "Bruine verglaçante", 57: "Bruine verglaçante",
    61: "Pluie légère", 63: "Pluie", 65: "Pluie forte",
    66: "Pluie verglaçante", 67: "Pluie verglaçante",
    71: "Neige légère", 73: "Neige", 75: "Neige forte", 77: "Grains de neige",
    80: "Averses légères", 81: "Averses", 82: "Averses violentes",
    85: "Averses de neige", 86: "Averses de neige fortes",
    95: "Orages", 96: "Orages et grêle", 99: "Orages violents et grêle",
}


class WeatherError(Exception):
    """Échec de l'appel à Open-Meteo."""


def _get(url: str, params: dict) -> dict:
    try:
        response = requests.get(url, params=params, timeout=REQUEST_TIMEOUT)
    except requests.RequestException as exc:
        raise WeatherError(f"Open-Meteo injoignable : {exc}") from exc
    if response.status_code != 200:
        raise WeatherError(f"Open-Meteo a répondu {response.status_code}.")
    try:
        return response.json()
    except ValueError as exc:
        raise WeatherError("Réponse Open-Meteo invalide.") from exc


def geocode(city: str, country: str = "") -> dict:
    """Ville (+ pays) -> {name, latitude, longitude}. WeatherError si introuvable."""
    query = f"{city} {country}".strip() if country else city
    data = _get(GEOCODING_URL, {"name": city, "count": 5, "language": "fr"})
    results = data.get("results") or []
    if country:
        wanted = country.strip().lower()
        results = sorted(
            results,
            key=lambda r: wanted not in (
                str(r.get("country", "")).lower(), str(r.get("country_code", "")).lower()
            ),
        )
    if not results:
        raise WeatherError(f"Ville introuvable : {query}.")
    top = results[0]
    return {"name": top.get("name", city), "latitude": top["latitude"], "longitude": top["longitude"]}


def _round(value, digits=1):
    return None if value is None else round(float(value), digits)


def normalize_forecast(raw: dict) -> dict:
    """Format interne stable : current, hourly (24 h, pas de 3 h), daily (8 jours)."""
    cur = raw.get("current") or {}
    hourly = raw.get("hourly") or {}
    times = hourly.get("time") or []

    def at(key, i):
        values = hourly.get(key) or []
        return values[i] if i < len(values) else None

    # Index de l'heure courante (les heures sont dans le fuseau du lieu).
    now_hour = str(cur.get("time", ""))[:13]
    start = next((i for i, t in enumerate(times) if str(t)[:13] >= now_hour), 0)

    hourly_points = []
    for i in range(start, min(start + 25, len(times)), 3):
        hourly_points.append({
            "time": times[i],
            "temp_c": _round(at("temperature_2m", i)),
            "precip_prob": at("precipitation_probability", i),
            "wind_kmh": _round(at("wind_speed_10m", i), 0),
            "code": at("weather_code", i),
        })

    daily = raw.get("daily") or {}
    daily_points = [
        {
            "date": d,
            "code": (daily.get("weather_code") or [None])[i],
            "temp_max_c": _round((daily.get("temperature_2m_max") or [None])[i], 0),
            "temp_min_c": _round((daily.get("temperature_2m_min") or [None])[i], 0),
        }
        for i, d in enumerate(daily.get("time") or [])
    ]

    code = cur.get("weather_code")
    return {
        "timezone": raw.get("timezone", ""),
        "current": {
            "time": cur.get("time"),
            "temp_c": _round(cur.get("temperature_2m")),
            "humidity": cur.get("relative_humidity_2m"),
            "wind_kmh": _round(cur.get("wind_speed_10m"), 0),
            "precip_prob": at("precipitation_probability", start),
            "code": code,
            "label": WMO_LABELS.get(code, ""),
        },
        "hourly": hourly_points,
        "daily": daily_points,
    }


def fetch_forecast(latitude: float, longitude: float) -> dict:
    raw = _get(FORECAST_URL, {
        "latitude": latitude,
        "longitude": longitude,
        "current": "temperature_2m,relative_humidity_2m,wind_speed_10m,weather_code",
        "hourly": "temperature_2m,precipitation_probability,wind_speed_10m,weather_code",
        "daily": "weather_code,temperature_2m_max,temperature_2m_min",
        "timezone": "auto",
        "forecast_days": 8,
    })
    return normalize_forecast(raw)
