"""
Tests des récitateurs hébergés LOCALEMENT (ex. Cheikh Abderrahmane Benmoussa) :
- catalogue local_reciters
- présence dans GET /quran/reciters/
- URL audio des chapitres servie depuis le frontend
- validation des identifiants (texte local accepté, inconnu rejeté)
"""
import pytest

from apps.quran import local_reciters

pytestmark = pytest.mark.django_db


class TestLocalReciterCatalog:
    def test_benmoussa_registered(self):
        reciter = local_reciters.get_local_reciter("benmoussa")
        assert reciter is not None
        assert reciter.name == "Cheikh Abderrahmane Benmoussa"
        assert reciter.slug == "benmoussa"

    def test_hssain_registered(self):
        reciter = local_reciters.get_local_reciter("hssain")
        assert reciter is not None
        assert reciter.name == "Cheikh Abdelhamid Hssain"
        assert reciter.slug == "hssain"
        assert reciter.riwaya == "Warsh"

    def test_unknown_returns_none(self):
        assert local_reciters.get_local_reciter("inconnu") is None
        assert local_reciters.get_local_reciter(None) is None
        assert local_reciters.get_local_reciter("") is None

    def test_chapter_path_zero_padded(self):
        reciter = local_reciters.get_local_reciter("benmoussa")
        assert local_reciters.chapter_path(reciter, 1) == "/quran/benmoussa/001.mp3"
        assert local_reciters.chapter_path(reciter, 114) == "/quran/benmoussa/114.mp3"

    def test_as_list_shape(self):
        items = local_reciters.as_list()
        assert len(items) >= 1
        entry = items[0]
        assert entry["local"] is True
        assert set(entry) >= {"id", "name", "style", "source", "local"}


class TestRecitersEndpointIncludesLocal:
    def test_local_reciter_listed(self, api_client):
        resp = api_client.get("/api/v1/quran/reciters/")
        # Le catalogue Quran.com peut être indisponible hors ligne : on teste
        # seulement la présence du récitateur local quand l'appel réussit.
        if resp.status_code != 200:
            pytest.skip("Quran.com indisponible")
        ids = [r["id"] for r in resp.data["chapter"]]
        assert "benmoussa" in ids


class TestChapterAudioLocal:
    def test_benmoussa_chapter_audio(self, api_client):
        resp = api_client.get("/api/v1/quran/audio/chapter/1/", {"reciter_id": "benmoussa"})
        assert resp.status_code == 200, resp.data
        assert resp.data["audio_url"] == "/quran/benmoussa/001.mp3"

    def test_benmoussa_surah_114(self, api_client):
        resp = api_client.get("/api/v1/quran/audio/chapter/114/", {"reciter_id": "benmoussa"})
        assert resp.status_code == 200
        assert resp.data["audio_url"] == "/quran/benmoussa/114.mp3"

    def test_unknown_text_reciter_rejected(self, api_client):
        resp = api_client.get("/api/v1/quran/audio/chapter/1/", {"reciter_id": "inconnu"})
        assert resp.status_code == 400
        assert resp.data["error"]["code"] == "invalid_params"

    def test_numeric_reciter_still_works(self, api_client):
        """Les identifiants numériques (Quran.com) restent acceptés."""
        resp = api_client.get("/api/v1/quran/audio/chapter/1/", {"reciter_id": "999999"})
        # 999999 est inconnu côté Quran.com → 503 ou 400, jamais une erreur de
        # format. Le point critique : "999999" n'est PAS rejeté par la validation.
        assert resp.status_code in (400, 503)
        if resp.status_code == 400:
            assert "reciter_id inconnu" not in resp.data["error"]["message"]

class TestChapterAudioHssain:
    def test_hssain_chapter_audio(self, api_client):
        resp = api_client.get("/api/v1/quran/audio/chapter/2/", {"reciter_id": "hssain"})
        assert resp.status_code == 200, resp.data
        assert resp.data["audio_url"] == "/quran/hssain/002.mp3"

    def test_hssain_last_surah(self, api_client):
        resp = api_client.get("/api/v1/quran/audio/chapter/114/", {"reciter_id": "hssain"})
        assert resp.status_code == 200
        assert resp.data["audio_url"] == "/quran/hssain/114.mp3"
