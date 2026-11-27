"""
Tests du texte du Coran en base locale :
- commande d'import (idempotence, validation, erreurs) ;
- lecture locale par les vues SANS aucun appel à Quran.com ;
- repli sur Quran.com quand la base est vide ou incomplète.
"""
import pytest
import responses
from django.core.cache import cache
from django.core.management import call_command
from django.core.management.base import CommandError

from apps.quran.models import Surah, Verse, VerseTranslation
from apps.quran.services import local_text, quran_client

pytestmark = pytest.mark.django_db

API = quran_client.settings.QURAN_API_BASE_URL

CHAPTERS = {"chapters": [
    {"id": n, "name_simple": f"Sourate {n}", "name_arabic": f"س{n}",
     "verses_count": 2 if n == 1 else 1, "revelation_place": "makkah"}
    for n in range(1, 115)
]}


def verses_payload(surah: int, count: int) -> dict:
    """Payload by_chapter avec fr (31) et en (20) pour `count` versets."""
    return {"verses": [
        {
            "verse_number": i,
            "text_uthmani": f"آية {surah}:{i}",
            "translations": [
                {"resource_id": 31, "text": f"FR {surah}:{i}<sup foot_note=1>1</sup>"},
                {"resource_id": 20, "text": f"EN {surah}:{i}"},
            ],
        }
        for i in range(1, count + 1)
    ]}


@pytest.fixture(autouse=True)
def clean_cache():
    cache.clear()
    yield
    cache.clear()


def mock_import(surahs=(1, 2)):
    responses.add(responses.GET, f"{API}/chapters", json=CHAPTERS)
    for n in surahs:
        responses.add(
            responses.GET, f"{API}/verses/by_chapter/{n}",
            json=verses_payload(n, 2 if n == 1 else 1),
        )


def run_import(*args):
    call_command("import_quran_text", "--pause", "0", *args)


@pytest.fixture
def loaded_surah_1():
    """Sourate 1 complète en base (2 versets, fr + en) + 114 sourates de métadonnées."""
    Surah.objects.bulk_create([
        Surah(number=n, name_arabic=f"س{n}", name_transliterated=f"Sourate {n}",
              verses_count=2 if n == 1 else 1, revelation_place="makkah")
        for n in range(1, 115)
    ])
    for i in (1, 2):
        v = Verse.objects.create(surah_id=1, ayah_number=i, text_uthmani=f"آية 1:{i}")
        VerseTranslation.objects.create(verse=v, code="fr", resource_id=31, text=f"FR 1:{i}")
        VerseTranslation.objects.create(verse=v, code="en", resource_id=20, text=f"EN 1:{i}")


class TestImportCommand:
    @responses.activate
    def test_import_stores_text_and_translations(self):
        mock_import()
        run_import("--surah", "1", "--surah", "2")
        assert Surah.objects.count() == 2
        assert Verse.objects.count() == 3
        assert VerseTranslation.objects.count() == 6
        fr = VerseTranslation.objects.get(verse__surah_id=1, verse__ayah_number=1, code="fr")
        assert fr.text == "FR 1:1"            # note de bas de page retirée
        assert fr.resource_id == 31

    @responses.activate
    def test_import_is_idempotent(self):
        mock_import()
        run_import("--surah", "1")
        run_import("--surah", "1")
        assert Verse.objects.count() == 2
        assert VerseTranslation.objects.count() == 4

    @responses.activate
    def test_single_language(self):
        mock_import(surahs=(1,))
        run_import("--surah", "1", "--translations", "fr")
        assert set(VerseTranslation.objects.values_list("code", flat=True)) == {"fr"}

    @responses.activate
    def test_reset_clears_previous_data(self):
        mock_import()
        run_import("--surah", "1")
        run_import("--surah", "2", "--reset")
        assert list(Surah.objects.values_list("number", flat=True)) == [2]

    @responses.activate
    def test_incomplete_surah_aborts_without_writing(self):
        responses.add(responses.GET, f"{API}/chapters", json=CHAPTERS)
        responses.add(responses.GET, f"{API}/verses/by_chapter/1", json=verses_payload(1, 1))  # 1 au lieu de 2
        with pytest.raises(CommandError, match="2 attendus"):
            run_import("--surah", "1")
        assert Verse.objects.count() == 0

    def test_rejects_unknown_language_and_bad_surah(self):
        with pytest.raises(CommandError, match="non prises en charge"):
            run_import("--translations", "de")
        with pytest.raises(CommandError, match="entre 1 et 114"):
            run_import("--surah", "200")

    @responses.activate
    def test_api_down_raises_clean_error(self):
        responses.add(responses.GET, f"{API}/chapters", status=500)
        with pytest.raises(CommandError, match="indisponible"):
            run_import()


class TestLocalServing:
    """Avec la base chargée, aucune requête réseau n'est émise (responses lève sinon)."""

    @responses.activate
    def test_surah_list_from_db(self, api_client, loaded_surah_1):
        resp = api_client.get("/api/v1/quran/surahs/")
        assert resp.status_code == 200
        assert len(resp.data) == 114
        assert resp.data[0] == {
            "number": 1, "name_arabic": "س1", "name_transliterated": "Sourate 1",
            "verses_count": 2, "revelation_place": "makkah",
        }
        assert len(responses.calls) == 0

    @responses.activate
    def test_verses_from_db_same_shape_as_api(self, api_client, loaded_surah_1):
        resp = api_client.get("/api/v1/quran/surahs/1/", {"translations": "fr,en"})
        assert resp.status_code == 200
        assert [v["ayah_number"] for v in resp.data] == [1, 2]
        first = resp.data[0]
        assert first["text_uthmani"] == "آية 1:1"
        assert [(t["code"], t["text"], t["resource_id"]) for t in first["translations"]] == [
            ("en", "EN 1:1", 20), ("fr", "FR 1:1", 31),
        ]
        assert len(responses.calls) == 0

    @responses.activate
    def test_default_translation_is_french(self, api_client, loaded_surah_1):
        resp = api_client.get("/api/v1/quran/surahs/1/")
        assert [t["code"] for t in resp.data[0]["translations"]] == ["fr"]

    @responses.activate
    def test_no_translation_requested_returns_empty_list(self, api_client, loaded_surah_1):
        data = local_text.get_verses(1, [])
        assert data[0]["translations"] == []
        assert len(responses.calls) == 0

    @responses.activate
    def test_translation_order_matches_quran_com(self, api_client, loaded_surah_1):
        """Ordre par resource_id (en=20 avant fr=31), comme l'API, quel que soit l'ordre demandé."""
        for asked in ("fr,en", "en,fr"):
            resp = api_client.get("/api/v1/quran/surahs/1/", {"translations": asked})
            assert [t["code"] for t in resp.data[0]["translations"]] == ["en", "fr"]


class TestFallbackToQuranCom:
    @responses.activate
    def test_empty_db_falls_back_to_api(self, api_client):
        responses.add(responses.GET, f"{API}/verses/by_chapter/1", json=verses_payload(1, 2))
        resp = api_client.get("/api/v1/quran/surahs/1/", {"translations": "fr"})
        assert resp.status_code == 200
        assert len(responses.calls) == 1

    @responses.activate
    def test_missing_translation_falls_back_to_api(self, api_client, loaded_surah_1):
        VerseTranslation.objects.filter(code="en", verse__ayah_number=2).delete()
        responses.add(responses.GET, f"{API}/verses/by_chapter/1", json=verses_payload(1, 2))
        resp = api_client.get("/api/v1/quran/surahs/1/", {"translations": "fr,en"})
        assert resp.status_code == 200
        assert len(responses.calls) == 1

    @responses.activate
    def test_unknown_language_falls_back_to_api(self, api_client, loaded_surah_1):
        responses.add(responses.GET, f"{API}/verses/by_chapter/1", json=verses_payload(1, 2))
        resp = api_client.get("/api/v1/quran/surahs/1/", {"translations": "ar"})
        assert resp.status_code == 200
        assert len(responses.calls) == 1

    @responses.activate
    def test_incomplete_surah_falls_back_to_api(self, api_client, loaded_surah_1):
        Verse.objects.filter(surah_id=1, ayah_number=2).delete()
        responses.add(responses.GET, f"{API}/verses/by_chapter/1", json=verses_payload(1, 2))
        resp = api_client.get("/api/v1/quran/surahs/1/", {"translations": "fr"})
        assert resp.status_code == 200
        assert len(responses.calls) == 1

    @responses.activate
    def test_partial_surah_table_falls_back_for_list(self, api_client):
        Surah.objects.create(number=1, name_arabic="x", name_transliterated="x", verses_count=7)
        responses.add(responses.GET, f"{API}/chapters", json=CHAPTERS)
        resp = api_client.get("/api/v1/quran/surahs/")
        assert resp.status_code == 200
        assert len(responses.calls) == 1

    @responses.activate
    def test_disabled_flag_uses_api(self, api_client, loaded_surah_1, monkeypatch):
        monkeypatch.setenv("QURAN_LOCAL_TEXT_ENABLED", "false")
        responses.add(responses.GET, f"{API}/verses/by_chapter/1", json=verses_payload(1, 2))
        resp = api_client.get("/api/v1/quran/surahs/1/", {"translations": "fr"})
        assert resp.status_code == 200
        assert len(responses.calls) == 1
