"""
Client HTTP pour l'API Aladhan (horaires de prière).

L'API est publique : aucune clé n'est nécessaire. Tous les appels sont
effectués côté serveur ; le frontend ne connaît jamais l'URL d'Aladhan.

Endpoints utilisés :
  * GET /v1/timings/{date}?latitude=&longitude=&method=&school=
  * GET /v1/timingsByCity?city=&country=&date=&method=&school=
"""
import re
from datetime import datetime

import requests
from django.conf import settings

REQUEST_TIMEOUT = 10  # secondes

# Madhhab interne -> valeur du paramètre `school` d'Aladhan.
SCHOOL_MAP = {"standard": 0, "hanafi": 1}


class AladhanError(Exception):
    """Échec de l'appel à Aladhan (réseau, statut HTTP, payload invalide)."""


def _clean_timing(value: str) -> str:
    """Supprime les suffixes entre parenthèses : "05:23 (+01:00)" -> "05:23"."""
    return re.sub(r"\s*\(.*\)$", "", str(value)).strip()


def _normalize_hijri(hijri: dict) -> dict:
    """Normalise le bloc date hégirien d'Aladhan en un format interne stable."""
    month = hijri.get("month") or {}
    return {
        "date": hijri.get("date", ""),
        "day": str(hijri.get("day", "")),
        "year": str(hijri.get("year", "")),
        "month": {
            "number": month.get("number"),
            "name": month.get("en", ""),
            "name_ar": month.get("ar", ""),
        },
    }


def _normalize_payload(data: dict) -> dict:
    """
    Transforme `data` d'Aladhan en format interne stable :
      {fajr, sunrise, dhuhr, asr, maghrib, isha, hijri_date, timezone}
    """
    timings = data.get("timings") or {}
    return {
        "fajr": _clean_timing(timings.get("Fajr", "")),
        "sunrise": _clean_timing(timings.get("Sunrise", "")),
        "dhuhr": _clean_timing(timings.get("Dhuhr", "")),
        "asr": _clean_timing(timings.get("Asr", "")),
        "maghrib": _clean_timing(timings.get("Maghrib", "")),
        "isha": _clean_timing(timings.get("Isha", "")),
        "hijri_date": _normalize_hijri(data.get("date", {}).get("hijri") or {}),
        "timezone": (data.get("meta") or {}).get("timezone", ""),
    }


def fetch_prayer_times(
    *,
    date_iso: str,
    latitude: float | None = None,
    longitude: float | None = None,
    city: str | None = None,
    country: str | None = None,
    method: int,
    madhhab: str,
) -> dict:
    """
    Appelle Aladhan et retourne les horaires normalisés.

    `date_iso` est au format ISO (YYYY-MM-DD) ; il est converti au format
    DD-MM-YYYY attendu par l'API Aladhan.
    """
    date_str = datetime.strptime(date_iso, "%Y-%m-%d").strftime("%d-%m-%Y")
    school = SCHOOL_MAP.get(madhhab, 0)

    params = {"method": method, "school": school}

    if city:
        url = f"{settings.ALADHAN_API_BASE_URL}/timingsByCity"
        params.update({"city": city, "country": country or "", "date": date_str})
    else:
        url = f"{settings.ALADHAN_API_BASE_URL}/timings/{date_str}"
        params.update({"latitude": latitude, "longitude": longitude})

    try:
        response = requests.get(url, params=params, timeout=REQUEST_TIMEOUT)
    except requests.RequestException as exc:
        raise AladhanError(f"Aladhan injoignable : {exc}") from exc

    if response.status_code != 200:
        raise AladhanError(f"Aladhan a répondu {response.status_code}.")

    try:
        payload = response.json()
    except ValueError as exc:
        raise AladhanError("Réponse Aladhan illisible.") from exc

    if payload.get("status") != "OK":
        raise AladhanError(
            f"Aladhan a signalé une erreur : {payload.get('status')}."
        )

    data = payload.get("data") or {}
    if not data.get("timings"):
        raise AladhanError("Aladhan n'a pas renvoyé d'horaires.")

    return _normalize_payload(data)
