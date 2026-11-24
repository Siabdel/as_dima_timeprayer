"""
Jours fériés légaux en France (métropole), par année grégorienne.

Fêtes à date fixe + fêtes mobiles calculées depuis Pâques (algorithme
grégorien anonyme de Meeus/Jones/Butcher, sans dépendance externe).
Jours supplémentaires propres à l'Alsace-Moselle signalés `regional=True`.
"""
from datetime import date, timedelta


def easter_sunday(year: int) -> date:
    """Dimanche de Pâques (calendrier grégorien)."""
    a = year % 19
    b, c = divmod(year, 100)
    d, e = divmod(b, 4)
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i, k = divmod(c, 4)
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    month, day = divmod(h + l - 7 * m + 114, 31)
    return date(year, month, day + 1)


def french_holidays(year: int) -> list[dict]:
    """Liste triée des jours fériés : {id, name, date, description, regional}."""
    easter = easter_sunday(year)
    items = [
        ("new-year", "Jour de l'An", date(year, 1, 1), "Premier jour de l'année.", False),
        ("good-friday", "Vendredi saint", easter - timedelta(days=2),
         "Férié uniquement en Alsace-Moselle.", True),
        ("easter-monday", "Lundi de Pâques", easter + timedelta(days=1),
         "Lendemain du dimanche de Pâques (date mobile).", False),
        ("labour-day", "Fête du Travail", date(year, 5, 1), "Fête internationale des travailleurs.", False),
        ("victory-1945", "Victoire 1945", date(year, 5, 8), "Commémoration de la fin de la Seconde Guerre mondiale en Europe.", False),
        ("ascension", "Ascension", easter + timedelta(days=39), "Jeudi, 39 jours après Pâques (date mobile).", False),
        ("whit-monday", "Lundi de Pentecôte", easter + timedelta(days=50), "Lendemain de la Pentecôte (date mobile).", False),
        ("national-day", "Fête nationale", date(year, 7, 14), "Fête nationale française (prise de la Bastille, 1789).", False),
        ("assumption", "Assomption", date(year, 8, 15), "Fête religieuse chrétienne.", False),
        ("all-saints", "Toussaint", date(year, 11, 1), "Fête religieuse chrétienne.", False),
        ("armistice-1918", "Armistice 1918", date(year, 11, 11), "Commémoration de l'armistice de la Première Guerre mondiale.", False),
        ("christmas", "Noël", date(year, 12, 25), "Fête religieuse chrétienne.", False),
        ("st-stephen", "Saint-Étienne", date(year, 12, 26), "Férié uniquement en Alsace-Moselle.", True),
    ]
    return [
        {"id": f"fr-{key}", "name": name, "date": d, "description": desc, "regional": regional}
        for key, name, d, desc, regional in sorted(items, key=lambda x: x[2])
    ]
