"""
Récitateurs dont l'audio est hébergé par l'application elle-même.

Contrairement aux récitateurs Quran.com (streamés depuis leurs serveurs),
ces récitations sont servies par le frontend (`frontend/public/quran/<slug>/`),
ce qui garantit la disponibilité et évite toute dépendance externe.

Ajouter un récitateur local :
  1. Déposer les MP3 dans frontend/public/quran/<slug>/001.mp3 … 114.mp3
  2. Ajouter une entrée dans LOCAL_RECITERS ci-dessous.
"""

import os
from dataclasses import dataclass

# Désactivable par environnement (LOCAL_RECITERS_ENABLED=false) quand les MP3
# ne sont pas déployés (ex. VPS sans les 816 Mo de Benmoussa).
def _enabled() -> bool:
    return os.environ.get("LOCAL_RECITERS_ENABLED", "true").lower() != "false"


def available_surahs() -> set[int] | None:
    """
    Sourates dont les MP3 sont déployés (LOCAL_RECITERS_SURAHS="100-114" ou
    "1,2,100-114"). None = toutes (114). Permet de ne livrer qu'une partie de
    l'audio (ex. les petites sourates) sans casser les autres.
    """
    raw = os.environ.get("LOCAL_RECITERS_SURAHS", "").strip()
    if not raw:
        return None
    result: set[int] = set()
    for part in raw.split(","):
        part = part.strip()
        if "-" in part:
            a, _, b = part.partition("-")
            if a.strip().isdigit() and b.strip().isdigit():
                result.update(range(int(a), int(b) + 1))
        elif part.isdigit():
            result.add(int(part))
    return {n for n in result if 1 <= n <= 114} or None


def surahs_label(surahs: set[int] | None) -> str:
    """« sourates 100-114 » (plages compactées), vide si toutes."""
    if not surahs:
        return ""
    nums, ranges, start = sorted(surahs), [], None
    for i, n in enumerate(nums):
        if start is None:
            start = prev = n
        elif n == prev + 1:
            prev = n
        else:
            ranges.append((start, prev))
            start = prev = n
        if i == len(nums) - 1:
            ranges.append((start, prev))
    text = ", ".join(f"{a}-{b}" if a != b else str(a) for a, b in ranges)
    return f"sourates {text}"


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
    if not reciter_id or not _enabled():
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
    if not _enabled():
        return []
    label = surahs_label(available_surahs())
    return [
        {
            "id": r.id,
            "name": r.name,
            "style": f"{r.riwaya} · {label}" if label else r.riwaya,
            "source": r.source,
            "local": True,
        }
        for r in LOCAL_RECITERS
    ]