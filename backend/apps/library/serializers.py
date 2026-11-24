"""Serializers de l'app library (douâas et hadiths)."""
from rest_framework import serializers

from .models import Dua, Hadith

# Catégories exposées avec leur libellé français (affiché par le frontend).
DUA_CATEGORY_LABELS = {
    "reveil": "Réveil & sommeil",
    "repas": "Repas",
    "maison": "Maison",
    "mosquee": "Mosquée",
    "protection": "Protection",
    "pardon": "Pardon & repentir",
    "vie": "Vie quotidienne",
}

HADITH_CATEGORY_LABELS = {
    "foi": "Foi & intentions",
    "priere": "Prière & culte",
    "morale": "Morale & comportement",
    "bienfaisance": "Bienfaisance",
    "relations": "Relations & famille",
}


class DuaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Dua
        fields = ["id", "category", "title", "text_ar", "transliteration",
                  "translation_fr", "source", "order"]


class HadithSerializer(serializers.ModelSerializer):
    class Meta:
        model = Hadith
        fields = ["id", "category", "title", "text_ar", "translation_fr",
                  "narrator", "source", "order"]
