"""
Tests de l'app library :
- seed_library (commande de gestion) : contenu chargé, idempotence
- endpoints douâas / hadiths / catégories (publics, filtrables)
- intégrité du contenu : texte arabe présent, source citée
"""
import pytest
from django.core.management import call_command
from django.urls import reverse

from apps.library.models import Dua, Hadith

pytestmark = pytest.mark.django_db

DUAS_URL = "/api/v1/library/duas/"
HADITHS_URL = "/api/v1/library/hadiths/"
CATEGORIES_URL = "/api/v1/library/categories/"


@pytest.fixture(autouse=True)
def seeded_library(db):
    """Contenu chargé avant chaque test."""
    call_command("seed_library")


class TestSeedLibrary:
    def test_content_loaded(self):
        assert Dua.objects.count() == 19
        assert Hadith.objects.count() == 19

    def test_source_title_pairs_unique(self):
        """Chaque couple (source, titre) est unique (clé d'idempotence du seed)."""
        # Deux douâas peuvent partager une source (ex. Sahîh Muslim 713 :
        # entrée ET sortie de la mosquée) — le couple (source, titre) est
        # la clé d'idempotence du seed.
        assert (
            Dua.objects.values("source", "title").distinct().count()
            == Dua.objects.count()
        )
        assert (
            Hadith.objects.values("source", "title").distinct().count()
            == Hadith.objects.count()
        )

    def test_idempotent(self):
        """Re-seed : aucun doublon."""
        call_command("seed_library")
        assert Dua.objects.count() == 19
        assert Hadith.objects.count() == 19

    def test_all_entries_have_arabic_text_and_translation(self):
        for dua in Dua.objects.all():
            assert dua.text_ar.strip(), f"Douâa sans texte arabe : {dua.title}"
            assert dua.translation_fr.strip(), f"Douâa sans traduction : {dua.title}"
            assert dua.source.strip(), f"Douâa sans source : {dua.title}"
        for hadith in Hadith.objects.all():
            assert hadith.text_ar.strip(), f"Hadith sans texte arabe : {hadith.title}"
            assert hadith.translation_fr.strip(), f"Hadith sans traduction : {hadith.title}"
            assert hadith.narrator.strip(), f"Hadith sans narrateur : {hadith.title}"
            assert hadith.source.strip(), f"Hadith sans source : {hadith.title}"


class TestLibraryEndpoints:
    def test_duas_public(self, api_client):
        resp = api_client.get(DUAS_URL)
        assert resp.status_code == 200
        assert resp.data["count"] == 19
        first = resp.data["results"][0]
        for field in ("id", "category", "title", "text_ar", "translation_fr", "source"):
            assert field in first

    def test_duas_filtered_by_category(self, api_client):
        resp = api_client.get(DUAS_URL, {"category": "repas"})
        assert resp.status_code == 200
        assert len(resp.data["results"]) >= 2
        assert all(d["category"] == "repas" for d in resp.data["results"])

    def test_duas_unknown_category_returns_empty(self, api_client):
        resp = api_client.get(DUAS_URL, {"category": "inconnu"})
        assert resp.status_code == 200
        assert resp.data["results"] == []

    def test_hadiths_public(self, api_client):
        resp = api_client.get(HADITHS_URL)
        assert resp.status_code == 200
        assert resp.data["count"] == 19
        first = resp.data["results"][0]
        for field in ("id", "category", "title", "text_ar", "translation_fr",
                      "narrator", "source"):
            assert field in first

    def test_hadiths_filtered_by_category(self, api_client):
        resp = api_client.get(HADITHS_URL, {"category": "foi"})
        assert resp.status_code == 200
        assert len(resp.data["results"]) >= 2
        assert all(h["category"] == "foi" for h in resp.data["results"])

    def test_categories_endpoint(self, api_client):
        resp = api_client.get(CATEGORIES_URL)
        assert resp.status_code == 200
        dua_keys = {c["key"] for c in resp.data["duas"]}
        hadith_keys = {c["key"] for c in resp.data["hadiths"]}
        assert dua_keys == {"reveil", "repas", "maison", "mosquee",
                            "protection", "pardon", "vie"}
        assert hadith_keys == {"foi", "priere", "morale", "bienfaisance", "relations"}
        assert all(c["label"] for c in resp.data["duas"] + resp.data["hadiths"])
