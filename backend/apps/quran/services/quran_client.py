"""
Client HTTP pour la Quran Foundation API v4 (api.quran.com).

Tous les appels se font côté serveur : les identifiants QURAN_CLIENT_ID /
QURAN_CLIENT_SECRET ne sont jamais exposés au frontend.

Texte arabe : script Uthmani (text_uthmani). Traductions : identifiants de
ressources Quran.com (ex. 31 = français Hamidullah, 20 = anglais Saheeh).
Les notes de bas de page HTML (<sup foot_note=...>) sont retirées du texte.

Le texte coranique et les métadonnées des sourates étant statiques, le cache
est long (24 h) : la charge sur l'API externe reste minimale même lors des
pics de traffic Ramadan.
"""
import logging
import re

import requests
from django.conf import settings

logger = logging.getLogger(__name__)

REQUEST_TIMEOUT = 15  # secondes

# Préfixe des chemins audio relatifs renvoyés pour les versets isolés.
VERSE_AUDIO_BASE_URL = "https://verses.quran.com/"

# Traductions supportées : code langue -> resource_id Quran.com v4
# (IDs vérifiés via /api/v4/resources/translations : 31 = Hamidullah français,
# 20 = Saheeh International anglais, 2 = Simplified Arabic).
TRANSLATION_IDS = {
    "fr": 31,   # Muhammad Hamidullah
    "en": 20,   # Saheeh International
    "ar": 2,    # Simplified Arabic
}


class QuranAPIError(Exception):
    """Échec de l'appel à la Quran Foundation API."""


def _get(path: str, params: dict | None = None) -> dict:
    """Appel GET authentifié si des identifiants sont configurés."""
    url = f"{settings.QURAN_API_BASE_URL}{path}"
    headers = {"Accept": "application/json"}
    if settings.QURAN_CLIENT_ID and settings.QURAN_CLIENT_SECRET:
        try:
            token = _get_access_token()
            headers["Authorization"] = f"Bearer {token}"
        except QuranAPIError:
            logger.warning("Token Quran.com indisponible — appel anonyme.")
    try:
        response = requests.get(url, params=params, headers=headers, timeout=REQUEST_TIMEOUT)
    except requests.RequestException as exc:
        raise QuranAPIError(f"Quran.com injoignable : {exc}") from exc
    if response.status_code != 200:
        raise QuranAPIError(f"Quran.com a répondu {response.status_code}.")
    try:
        return response.json()
    except ValueError as exc:
        raise QuranAPIError("Réponse Quran.com illisible.") from exc


def _get_access_token() -> str:
    """Obtient un jeton OAuth2 si des identifiants Quran Foundation sont fournis."""
    try:
        response = requests.post(
            "https://oauth.quran.foundation/oauth2/token",
            data={"grant_type": "client_credentials"},
            auth=(settings.QURAN_CLIENT_ID, settings.QURAN_CLIENT_SECRET),
            timeout=REQUEST_TIMEOUT,
        )
    except requests.RequestException as exc:
        raise QuranAPIError(f"OAuth Quran.com injoignable : {exc}") from exc
    if response.status_code != 200:
        raise QuranAPIError(f"OAuth Quran.com a répondu {response.status_code}.")
    token = response.json().get("access_token")
    if not token:
        raise QuranAPIError("Aucun access_token dans la réponse OAuth.")
    return token


# ---------------------------------------------------------------------------
# Normalisation
# ---------------------------------------------------------------------------

def normalize_chapters(payload: dict) -> list[dict]:
    """Convertit la liste des chapitres Quran.com en format interne stable."""
    chapters = []
    for ch in payload.get("chapters", []):
        chapters.append({
            "number": ch.get("id"),
            "name_arabic": ch.get("name_arabic", ""),
            "name_transliterated": ch.get("name_simple", ""),
            "verses_count": ch.get("verses_count", 0),
            "revelation_place": ch.get("revelation_place", ""),  # "makkah" | "madinah"
        })
    return chapters


def normalize_verses(payload: dict, code_by_resource: dict | None = None) -> list[dict]:
    """
    Convertit les versets Quran.com en format interne stable.

    L'API v4 ne renvoie pas de nom de langue dans les traductions : le code
    (« fr », « en »…) est donc dérivé de la correspondance resource_id ->
    code établie au moment de la requête. Les notes de bas de page HTML
    (<sup foot_note=...>) sont retirées pour un rendu propre côté frontend.
    """
    code_by_resource = code_by_resource or {}

    def _clean(text: str) -> str:
        return re.sub(r"<sup[^>]*>.*?</sup>", "", text or "").strip()

    verses = []
    for v in payload.get("verses", []):
        translations = [
            {
                "code": code_by_resource.get(tr.get("resource_id"), tr.get("language_name", "")),
                "text": _clean(tr.get("text", "")),
                "resource_id": tr.get("resource_id"),
            }
            for tr in v.get("translations", [])
        ]
        verses.append({
            "ayah_number": v.get("verse_number"),
            "text_uthmani": _clean(v.get("text_uthmani", "")),
            "translations": translations,
        })
    return verses


def normalize_reciters(payload: dict) -> dict:
    """
    Sépare les récitateurs « chapitre » (lecture continue) et « verset »
    (récitation par verset) comme demandé par le cahier des charges.
    """
    chapter_reciters, verse_reciters = [], []
    for rec in payload.get("recitations", []):
        entry = {
            "id": rec.get("id"),
            "name": rec.get("name", ""),
            "style": rec.get("style", ""),
        }
        if rec.get("relative_path") and "per_ayaah" in str(rec.get("relative_path")):
            verse_reciters.append(entry)
        else:
            chapter_reciters.append(entry)
    return {"chapter": chapter_reciters, "verse": verse_reciters}


# ---------------------------------------------------------------------------
# API publique du module
# ---------------------------------------------------------------------------

def fetch_surahs() -> list[dict]:
    """Liste des 114 sourates."""
    return normalize_chapters(_get("/chapters"))


def fetch_verses(surah: int, translations: list[str]) -> list[dict]:
    """
    Versets d'une sourate : texte arabe Uthmani + traductions demandées
    (ex. translations=["fr", "en"]).
    """
    code_by_resource = {
        resource_id: code for code, resource_id in TRANSLATION_IDS.items()
    }
    translation_ids = ",".join(str(TRANSLATION_IDS.get(t, t)) for t in translations)
    params = {
        "fields": "text_uthmani",
        "translations": translation_ids,
        "per_page": 300,  # une sourate n'a jamais plus de 286 versets
    }
    return normalize_verses(_get(f"/verses/by_chapter/{surah}", params), code_by_resource)


def fetch_reciters() -> dict:
    """Liste des récitateurs, séparés chapitre / verset."""
    return normalize_reciters(_get("/resources/recitations"))


# ---------------------------------------------------------------------------
# Lecture mot à mot (Word-by-Word)
# ---------------------------------------------------------------------------
def normalize_words(payload_verse: dict) -> list[dict]:
    """
    Convertit les `words` d'un verset Quran.com en format interne stable.

    Champs par mot :
      * position      — ordre dans le verset (1, 2, 3…)
      * text_uthmani  — mot en script Uthmani
      * translation_fr — traduction française (lexique local) ou, à défaut,
                         la traduction anglaise fournie par Quran.com
      * translation_en — traduction anglaise de Quran.com (toujours présente)
      * transliteration — translittération latine (Quran.com)
      * audio_url     — URL absolue du MP3 du mot isolé (verses.quran.com/wbw)
      * is_end        — true pour le marqueur de fin de verset (numéro)
    """
    from .lexicon_fr import translate_word

    words = []
    for w in payload_verse.get("words", []):
        char_type = w.get("char_type_name")
        arabic = w.get("text_uthmani") or w.get("text") or ""
        audio_relative = w.get("audio_url") or ""
        english = ((w.get("translation") or {}).get("text") or "").strip()

        # Traduction française : lexique local d'abord, sinon anglais.
        french = translate_word(arabic) if char_type == "word" else None
        if not french:
            french = english

        words.append(
            {
                "position": w.get("position"),
                "text_uthmani": arabic,
                "translation_fr": french,
                "translation_en": english,
                "transliteration": ((w.get("transliteration") or {}).get("text") or "").strip(),
                "audio_url": f"{VERSE_AUDIO_BASE_URL}{audio_relative}" if audio_relative else "",
                "is_end": char_type == "end",
            }
        )
    return words


def fetch_verse_words(surah: int, ayah: int) -> dict:
    """
    Mots d'un verset (lecture mot à mot) : GET /verses/by_key/{s}:{a}?words=true.

    Retourne {"verse_key": "2:255", "words": [...]}.
    """
    params = {
        "words": "true",
        "word_fields": "text_uthmani,translation,transliteration,audio_url",
    }
    payload = _get(f"/verses/by_key/{surah}:{ayah}", params)
    verse = payload.get("verse") or {}
    return {
        "verse_key": verse.get("verse_key") or f"{surah}:{ayah}",
        "words": normalize_words(verse),
    }


def fetch_chapter_words(surah: int) -> list[dict]:
    """
    Mots de TOUS les versets d'une sourate — GET /verses/by_chapter/{n}
    avec words=true. Utilisé par la lecture mot à mot de la sourate entière.

    Retourne une liste de {"ayah_number", "verse_key", "words": [...]}.
    """
    params = {
        "fields": "text_uthmani",
        "words": "true",
        "word_fields": "text_uthmani,translation,transliteration,audio_url",
        "per_page": 300,
    }
    payload = _get(f"/verses/by_chapter/{surah}", params)
    result = []
    for verse in payload.get("verses", []):
        result.append(
            {
                "ayah_number": verse.get("verse_number"),
                "verse_key": verse.get("verse_key"),
                "words": normalize_words(verse),
            }
        )
    return result


def fetch_chapter_audio(surah: int, reciter_id: int) -> dict:
    """URL audio de la sourate complète pour un réciteur donné."""
    # segments=true : horodatages par verset (et par mot) pour le suivi visuel.
    payload = _get(f"/chapter_recitations/{reciter_id}/{surah}", {"segments": "true"})
    # L'API v4 imbrique l'URL : {"audio_file": {"audio_url": "https://..."}}
    audio_file = payload.get("audio_file") or {}
    audio_url = audio_file.get("audio_url")
    if not audio_url:
        raise QuranAPIError("Aucune URL audio pour cette sourate.")
    return {
        "audio_url": audio_url,
        "timestamps": normalize_timestamps(audio_file.get("timestamps")),
    }


def normalize_timestamps(raw) -> list[dict]:
    """
    Normalise les horodatages d'un audio chapitre (ms) :
    [{ayah, from, to, segments: [[position_mot, début, fin], ...]}].
    Les entrées invalides sont ignorées (le suivi se dégrade, jamais d'erreur).
    """
    result = []
    for item in raw or []:
        try:
            ayah = int(str(item.get("verse_key", "")).split(":")[1])
            start = int(item["timestamp_from"])
            end = int(item["timestamp_to"])
        except (AttributeError, IndexError, KeyError, TypeError, ValueError):
            continue
        segments = []
        for seg in item.get("segments") or []:
            try:
                segments.append([int(seg[0]), int(seg[1]), int(seg[2])])
            except (IndexError, TypeError, ValueError):
                continue
        result.append({"ayah": ayah, "from": start, "to": end, "segments": segments})
    return result


def fetch_verse_audio(surah: int, ayah: int, reciter_id: int) -> dict:
    """
    URL audio du verset pour un réciteur + timings des segments si disponibles
    (utile pour le surlignage de la lecture en cours).
    """
    payload = _get(f"/recitations/{reciter_id}/by_ayah/{surah}:{ayah}")
    files = payload.get("audio_files") or []
    first = files[0] if files else {}
    rel_url = first.get("url")
    if not rel_url:
        raise QuranAPIError("Aucune URL audio pour ce verset.")
    # L'API renvoie un chemin relatif (ex. « Alafasy/mp3/001001.mp3 »).
    audio_url = rel_url if rel_url.startswith("http") else f"{VERSE_AUDIO_BASE_URL}{rel_url.lstrip('/')}"
    return {
        "audio_url": audio_url,
        "timings": {"segments": first.get("segments") or []},
    }
