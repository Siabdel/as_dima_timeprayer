"""
Conversion grégorien -> hégirien.

Source primaire : la réponse Aladhan (bloc `hijri` déjà normalisé par
l'app prayer_times). Source de secours : la bibliothèque `hijridate`
(calendrier Umm al-Qura, fiable et hors-ligne).
"""
from datetime import date

from hijridate import Gregorian


def gregorian_to_hijri(date_obj: date) -> dict:
    """
    Convertit une date grégorienne en dictionnaire hégirien normalisé
    (même structure que le bloc hijri_date d'Aladhan).
    """
    hijri = Gregorian(date_obj.year, date_obj.month, date_obj.day).to_hijri()
    return {
        "date": f"{hijri.day:02d}-{hijri.month:02d}-{hijri.year}",
        "day": str(hijri.day),
        "year": str(hijri.year),
        "month": {
            "number": hijri.month,
            "name": hijri.month_name("en"),
            "name_ar": hijri.month_name("ar"),
        },
    }
