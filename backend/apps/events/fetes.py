"""
Catalogue des fêtes religieuses islamiques et fêtes nationales marocaines.

Choix de conception : catalogue statique (constante Python) plutôt que modèle
en base — les dates sont soit grégoriennes fixes (fêtes nationales), soit
hégiriennes récurrentes (fêtes islamiques), recalculées chaque année via
`hijridate` (calendrier Umm al-Qura, hors-ligne, même bibliothèque que
l'endpoint /hijri/).

Fêtes nationales marocaines (officielles, dates grégoriennes fixes) :
  * 1er janvier   — Nouvel an
  * 11 janvier    — Manifeste de l'Indépendance
  * 1er mai       — Fête du Travail
  * 30 juillet    — Fête du Trône
  * 14 août       — Récupération d'Oued Ed-Dahab
  * 20 août       — Révolution du Roi et du Peuple
  * 21 août       — Fête de la Jeunesse
  * 6 novembre    — Marche Verte
  * 18 novembre   — Fête de l'Indépendance

Fêtes islamiques (dates hégiriennes, varient chaque année) :
  * 1 Muharram         — Nouvel an hégirien
  * 10 Muharram        — Achoura
  * 12 Rabi al-Awwal   — Mawlid an-Nabawi
  * 27 Rajab           — Isra & Mi'raj
  * 1 Ramadan          — Début du Ramadan
  * 27 Ramadan         — Laylat al-Qadr (probable)
  * 1 Shawwal          — Aïd al-Fitr
  * 9 Dhu al-Hijjah    — Jour d'Arafah
  * 10 Dhu al-Hijjah   — Aïd al-Adha
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class GregorianEvent:
    """Fête à date grégorienne fixe (ex. fêtes nationales marocaines)."""

    id: str
    name: str
    name_ar: str
    day: int    # 1-31
    month: int  # 1-12
    description: str


@dataclass(frozen=True)
class HijriEvent:
    """Fête islamique à date hégirienne récurrente."""

    id: str
    name: str
    name_ar: str
    hijri_day: int      # 1-30
    hijri_month: int    # 1-12
    description: str


# ---------------------------------------------------------------------------
# Fêtes nationales marocaines (ordre chronologique de l'année)
# ---------------------------------------------------------------------------
MOROCCAN_EVENTS: list[GregorianEvent] = [
    GregorianEvent(
        "new-year", "Nouvel an", "رأس السنة", 1, 1,
        "Premier jour de l'année grégorienne (jour férié au Maroc).",
    ),
    GregorianEvent(
        "independence-manifesto", "Manifeste de l'Indépendance", "ذكرى تقديم وثيقة الاستقلال", 11, 1,
        "Anniversaire du Manifeste de l'Indépendance du 11 janvier 1944.",
    ),
    GregorianEvent(
        "labour-day", "Fête du Travail", "عيد الشغل", 1, 5,
        "Journée internationale des travailleurs (jour férié au Maroc).",
    ),
    GregorianEvent(
        "throne-day", "Fête du Trône", "عيد العرش", 30, 7,
        "Principale fête nationale : anniversaire de l'accession au trône du Roi Mohammed VI (30 juillet 1999).",
    ),
    GregorianEvent(
        "oued-ed-dahab", "Récupération d'Oued Ed-Dahab", "ذكرى استرجاع وادي الذهب", 14, 8,
        "Anniversaire de la récupération d'Oued Ed-Dahab (14 août 1979).",
    ),
    GregorianEvent(
        "revolution-king-people", "Révolution du Roi et du Peuple", "ذكرى ثورة الملك والشعب", 20, 8,
        "Anniversaire de la Révolution du Roi et du Peuple (20 août 1953).",
    ),
    GregorianEvent(
        "youth-day", "Fête de la Jeunesse", "عيد الشباب", 21, 8,
        "Anniversaire de la naissance du Roi Mohammed VI (21 août 1963).",
    ),
    GregorianEvent(
        "green-march", "Marche Verte", "المسيرة الخضراء", 6, 11,
        "Anniversaire de la Marche Verte (6 novembre 1975).",
    ),
    GregorianEvent(
        "independence-day", "Fête de l'Indépendance", "عيد الاستقلال", 18, 11,
        "Anniversaire de l'indépendance du Maroc (18 novembre 1956).",
    ),
]

# ---------------------------------------------------------------------------
# Fêtes islamiques (dates hégiriennes)
# ---------------------------------------------------------------------------
ISLAMIC_EVENTS: list[HijriEvent] = [
    HijriEvent(
        "hijri-new-year", "Nouvel an hégirien", "رأس السنة الهجرية", 1, 1,
        "Premier jour de l'année hégirienne (Muharram).",
    ),
    HijriEvent(
        "ashura", "Achoura", "يوم عاشوراء", 10, 1,
        "10 Muharram — jour de jeûne recommandé (surérogatoire).",
    ),
    HijriEvent(
        "mawlid", "Mawlid an-Nabawi", "المولد النبوي الشريف", 12, 3,
        "Naissance du Prophète ﷺ (12 Rabi al-Awwal).",
    ),
    HijriEvent(
        "isra-miraj", "Isra & Mi'raj", "الإسراء والمعراج", 27, 7,
        "Voyage nocturne du Prophète ﷺ de La Mecque à Jérusalem et aux cieux (27 Rajab).",
    ),
    HijriEvent(
        "ramadan-start", "Début du Ramadan", "بداية شهر رمضان", 1, 9,
        "Premier jour du mois de Ramadan (mois du jeûne).",
    ),
    HijriEvent(
        "laylat-al-qadr", "Laylat al-Qadr", "ليلة القدر", 27, 9,
        "La Nuit du Destin — la plus probable des nuits impaires des 10 derniers jours de Ramadan.",
    ),
    HijriEvent(
        "eid-al-fitr", "Aïd al-Fitr", "عيد الفطر", 1, 10,
        "Fête de la rupture du jeûne, le lendemain de Ramadan (1 Shawwal).",
    ),
    HijriEvent(
        "arafah", "Jour d'Arafah", "يوم عرفة", 9, 12,
        "9 Dhu al-Hijjah — jour du grand pèlerinage, jeûne très recommandé pour celui qui n'effectue pas le Hajj.",
    ),
    HijriEvent(
        "eid-al-adha", "Aïd al-Adha", "عيد الأضحى", 10, 12,
        "Fête du sacrifice (10 Dhu al-Hijjah) — la plus grande des deux fêtes.",
    ),
]
