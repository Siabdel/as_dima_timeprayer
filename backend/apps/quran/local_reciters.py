"""
Récitateurs dont l'audio est hébergé par l'application elle-même.

Contrairement aux récitateurs Quran.com (streamés depuis leurs serveurs),
ces récitations sont servies par le frontend (`frontend/public/quran/<slug>/`),
ce qui garantit la disponibilité et évite toute dépendance externe.

Ajouter un récitateur local :
  1. Déposer les MP3 dans frontend/public/quran/<slug>/001.mp3 … 114.mp3
  2. Ajouter une entrée dans LOCAL_RECITERS ci-dessous.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class LocalReciter:
    """Un récitateur hébergé localement (chapitres complets)."""

    id: str            # identifiant utilisé dans l'API (reciter_id=<id>)
    name: str          # nom affiché
    slug: str          # dossier sous frontend/public/quran/
    riwaya: str        # lecture (Hafs, Warsh…)
    source: str        # crédit / provenance


LOCAL_RECITERS: list[LocalReciter] = [
    LocalReciter(
        id="benmoussa",
        name="Cheikh Abderrahmane Benmoussa",
        slug="benmoussa",
        riwaya="Hafs",
        source="archive.org — AbdulrahmanBenmoussa (64 kbps)",
    ),
    LocalReciter(
        id="hssain",
        name="Cheikh Abdelhamid Hssain",
        slug="hssain",
        riwaya="Warsh",
        source="archive.org — abdelhamed-hssain-warsh",
    ),
]

# Récitateurs locaux indexés par identifiant (lookup O(1)).
_BY_ID = {r.id: r for r in LOCAL_RECITERS}


def get_local_reciter(reciter_id: str | None) -> LocalReciter | None:
    """Retourne le récitateur local correspondant, ou None."""
    if not reciter_id:
        return None
    return _BY_ID.get(str(reciter_id))


def chapter_path(reciter: LocalReciter, surah: int) -> str:
    """
    Chemin RELATIF du MP3 d'une sourate pour un récitateur local.
    Les fichiers sont nommés 001.mp3 … 114.mp3.
    """
    return f"/quran/{reciter.slug}/{surah:03d}.mp3"


def as_list() -> list[dict]:
    """Liste sérialisée pour l'API (ajoutée à GET /quran/reciters/)."""
    return [
        {
            "id": r.id,
            "name": r.name,
            "style": r.riwaya,
            "source": r.source,
            "local": True,
        }
        for r in LOCAL_RECITERS
    ]