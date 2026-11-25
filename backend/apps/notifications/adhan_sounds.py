"""
Catalogue des sons d'Adhan disponibles dans l'application.

Choix de conception : liste statique (constante Python) plutôt que modèle en
base — le catalogue est contrôlé par le code, identique pour tous les
utilisateurs, et le champ de préférence `UserPreference.adhan_sound_id` est
validé contre ces identifiants.

Sources (archive.org, item « adhan_202606 » — Adhan by different callers) :
  * Abdul Basit Abdus Samad     — légende égyptienne, adhan complet
  * Mishary Rashid Alafasy      — adhan Fajr (Koweït)
  * Muhammad Siddiq Al-Minshawi — légende égyptienne, adhan complet
  * La Mecque, Médine, Al-Aqsa (Jérusalem), Égypte — adhan complets (muezzin non
    précisé par la source : libellés par lieu). L'item archive.org ne mentionne
    aucune licence : à confirmer avant toute diffusion large.

Les fichiers MP3 sont hébergés par l'application elle-même
(`frontend/public/adhan/`) et servis depuis la même origine que l'app :
le service worker et l'aperçu dans les réglages n'ont aucun problème de CORS
et ne dépendent d'aucun serveur tiers.

Pour ajouter/retirer un son : ajouter une entrée dans SOUNDS et déposer le
fichier MP3 correspondant dans frontend/public/adhan/. L'URL est RELATIVE —
le navigateur la résout par rapport à l'origine de l'app.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class AdhanSound:
    """Un son d'Adhan proposé à l'utilisateur."""

    id: str          # identifiant stable (stocké dans UserPreference.adhan_sound_id)
    name: str        # libellé affiché (français)
    reciter: str     # nom du réciteur / muezzin
    url: str         # chemin relatif du MP3 (servi par le frontend)


SOUNDS: list[AdhanSound] = [
    AdhanSound(
        id="abdul-basit",
        name="Adhan complet",
        reciter="Abdul Basit Abdus Samad",
        url="/adhan/abdul-basit.mp3",
    ),
    AdhanSound(
        id="alafasy",
        name="Adhan Fajr",
        reciter="Mishary Rashid Alafasy",
        url="/adhan/alafasy.mp3",
    ),
    AdhanSound(
        id="minshawi",
        name="Adhan complet",
        reciter="Muhammad Siddiq Al-Minshawi",
        url="/adhan/minshawi.mp3",
    ),
    AdhanSound(
        id="makkah",
        name="Adhan de la Mecque",
        reciter="Masjid al-Haram (La Mecque)",
        url="/adhan/makkah.mp3",
    ),
    AdhanSound(
        id="madinah",
        name="Adhan de Médine",
        reciter="Masjid an-Nabawi (Médine)",
        url="/adhan/madinah.mp3",
    ),
    AdhanSound(
        id="alaqsa",
        name="Adhan d'Al-Aqsa",
        reciter="Masjid al-Aqsa (Jérusalem)",
        url="/adhan/alaqsa.mp3",
    ),
    AdhanSound(
        id="egypt",
        name="Adhan d'Égypte",
        reciter="Muezzin égyptien",
        url="/adhan/egypt.mp3",
    ),
]

# Son sélectionné par défaut quand l'utilisateur n'a pas fait de choix.
DEFAULT_SOUND_ID = "abdul-basit"


def get_sound(sound_id: str | None) -> AdhanSound | None:
    """Retourne le son correspondant à `sound_id`, ou None si inconnu/vide."""
    if not sound_id:
        return None
    return next((s for s in SOUNDS if s.id == sound_id), None)


def get_sound_url(sound_id: str | None) -> str:
    """
    URL du son d'Adhan à jouer pour l'utilisateur.

    Retourne l'URL du son choisi, ou celle du son par défaut si le champ
    est vide ou l'identifiant inconnu (robustesse : une préférence pointant
    vers un son retiré du catalogue ne doit jamais bloquer la notification).
    """
    return (get_sound(sound_id) or get_sound(DEFAULT_SOUND_ID)).url


def as_list() -> list[dict]:
    """Catalogue sérialisé pour l'API (GET /notifications/adhan-sounds/)."""
    return [
        {"id": s.id, "name": s.name, "reciter": s.reciter, "url": s.url}
        for s in SOUNDS
    ]
