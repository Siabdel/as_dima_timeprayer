"""Dates importantes de Ramadan, calculées à partir du calendrier du lieu."""
from datetime import date, timedelta


def _shift(iso: str, days: int) -> str:
    return (date.fromisoformat(iso) + timedelta(days=days)).isoformat()


def build_key_dates(days: list[dict]) -> list[dict]:
    """
    Dates clés à partir des jours (triés, `date` ISO, `hijri_day` 1..N).

    Une « nuit » hégirienne commence au coucher du soleil de la veille : la nuit
    du 27 Ramadan débute le soir du 26 (date grégorienne = celle du 26).
    Les dates dépendent de l'observation de la lune : elles peuvent varier d'un
    jour selon le pays.
    """
    by_day = {d["hijri_day"]: d["date"] for d in days}
    last_day = max(by_day)
    key: list[dict] = []

    def add(kind, name, name_ar, evening_of, day_num, description, highlight=False):
        if evening_of not in by_day:
            return
        key.append({
            "id": kind, "name": name, "name_ar": name_ar,
            "date": by_day[evening_of],
            "hijri_day": day_num,
            "night": True,
            "description": description,
            "highlight": highlight,
        })

    key.append({
        "id": "first-day", "name": "1er jour de Ramadan", "name_ar": "أول رمضان",
        "date": by_day[min(by_day)], "hijri_day": 1, "night": False,
        "description": "Premier jour de jeûne. La première prière de tarawih est récitée la veille au soir.",
        "highlight": True,
    })
    if 17 in by_day:
        key.append({
            "id": "badr", "name": "Bataille de Badr", "name_ar": "غزوة بدر",
            "date": by_day[17], "hijri_day": 17, "night": False,
            "description": "Anniversaire de la bataille de Badr (17 Ramadan, an 2 de l'Hégire).",
            "highlight": False,
        })
    add("last-ten", "Début des 10 dernières nuits", "العشر الأواخر", 20, 21,
        "Début de la retraite spirituelle (i'tikaf). La nuit du 21 est la première nuit impaire, "
        "candidate à la Nuit du Destin.")
    add("night-23", "Nuit du 23", "ليلة 23", 22, 23,
        "Nuit impaire des dix derniers jours, candidate à la Nuit du Destin.")
    add("night-25", "Nuit du 25", "ليلة 25", 24, 25,
        "Nuit impaire des dix derniers jours, candidate à la Nuit du Destin.")
    add("laylat-al-qadr", "Nuit du Destin (Laylat al-Qadr)", "ليلة القدر", 26, 27,
        "Nuit la plus attendue, « meilleure que mille mois » (Coran 97). Elle se cherche "
        "dans les nuits impaires des dix derniers jours ; la 27e est la plus souvent retenue.",
        highlight=True)
    add("night-29", "Nuit du 29", "ليلة 29", 28, 29,
        "Dernière nuit impaire des dix derniers jours.")

    eid = _shift(by_day[last_day], 1)
    key.append({
        "id": "eid-al-fitr", "name": "Aïd al-Fitr", "name_ar": "عيد الفطر",
        "date": eid, "hijri_day": None, "night": False,
        "description": "1er Chawwal : fin du jeûne. La zakat al-fitr se verse avant la prière de l'Aïd.",
        "highlight": True,
    })
    key.sort(key=lambda k: (k["date"], k["id"]))
    return key
