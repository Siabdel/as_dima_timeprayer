"""
Lecture du texte du Coran depuis la base locale (alternative à Quran.com).

Les sourates, versets et traductions sont importés une fois par
`python manage.py import_quran_text`. Tant qu'une donnée est absente (base
vide, traduction non importée, langue inconnue), ces fonctions renvoient None
et les vues retombent sur l'API Quran.com : l'application ne casse jamais.

Le format retourné est strictement celui de `quran_client` (voir
`normalize_chapters` / `normalize_verses`), donc le frontend ne change pas.

Désactivable : QURAN_LOCAL_TEXT_ENABLED=false.
"""
import os

from django.db.models import Count

from apps.quran.models import Surah, Verse, VerseTranslation


def enabled() -> bool:
    return os.environ.get("QURAN_LOCAL_TEXT_ENABLED", "true").lower() != "false"


def get_surahs() -> list[dict] | None:
    """Les 114 sourates, ou None si la base n'est pas complète."""
    if not enabled():
        return None
    rows = list(Surah.objects.order_by("number"))
    if len(rows) != 114:
        return None
    return [
        {
            "number": s.number,
            "name_arabic": s.name_arabic,
            "name_transliterated": s.name_transliterated,
            "verses_count": s.verses_count,
            "revelation_place": s.revelation_place,
        }
        for s in rows
    ]


def get_verses(surah: int, translations: list[str]) -> list[dict] | None:
    """
    Versets d'une sourate avec les traductions demandées (codes « fr », « en »).

    Renvoie None si la sourate n'est pas complète en base ou si une des
    traductions demandées n'est pas disponible pour tous ses versets.
    """
    if not enabled():
        return None
    try:
        expected = Surah.objects.values_list("verses_count", flat=True).get(number=surah)
    except Surah.DoesNotExist:
        return None
    verses = list(Verse.objects.filter(surah_id=surah).order_by("ayah_number"))
    if len(verses) != expected:
        return None

    codes = list(dict.fromkeys(translations))  # sans doublon
    by_verse: dict[int, dict[str, VerseTranslation]] = {v.id: {} for v in verses}
    if codes:
        rows = VerseTranslation.objects.filter(verse__surah_id=surah, code__in=codes)
        for tr in rows:
            by_verse[tr.verse_id][tr.code] = tr
        # Chaque verset doit avoir chaque traduction demandée.
        if any(code not in by_verse[v.id] for v in verses for code in codes):
            return None

    # Même ordre que Quran.com (par ID de ressource croissant, quel que soit
    # l'ordre demandé) : le frontend affiche les traductions dans l'ordre reçu.
    return [
        {
            "ayah_number": v.ayah_number,
            "text_uthmani": v.text_uthmani,
            "translations": [
                {"code": tr.code, "text": tr.text, "resource_id": tr.resource_id}
                for tr in sorted(by_verse[v.id].values(), key=lambda t: t.resource_id)
            ],
        }
        for v in verses
    ]


def stats() -> dict:
    """Résumé de ce qui est importé (pour la commande d'import et le debug)."""
    return {
        "surahs": Surah.objects.count(),
        "verses": Verse.objects.count(),
        "translations": dict(
            VerseTranslation.objects.values_list("code").annotate(n=Count("id")).order_by("code")
        ),
    }
