"""
Tests de l'app quran :
- normalisation des réponses Quran.com (sourates, versets, récitateurs)
- cache Redis (ne jamais rappeler Quran.com pour une requête déjà en cache)
- endpoints publics (sans JWT) + progression protégée
- gestion d'erreur (Quran.com indisponible → 503)
"""
import pytest
import responses
from django.core.cache import cache
from django.urls import reverse

from apps.quran.services import quran_client

pytestmark = pytest.mark.django_db

# Payload Quran.com minimal (structure réelle simplifiée)
CHAPTERS_PAYLOAD = {
    "chapters": [
        {
            "id": 1,
            "name_simple": "Al-Fatihah",
            "name_arabic": "الفاتحة",
            "verses_count": 7,
            "revelation_place": "makkah",
        },
        {
            "id": 2,
            "name_simple": "Al-Baqarah",
            "name_arabic": "البقرة",
            "verses_count": 286,
            "revelation_place": "madinah",
        },
    ]
}

VERSES_PAYLOAD = {
    "verses": [
        {
            "verse_number": 1,
            "text_uthmani": "بِسْمِ ٱللَّهِ ٱلرَّحْمَٰنِ ٱلرَّحِيمِ",
            "translations": [
                {"language_name": "french", "text": "Au nom d'Allah, le Tout Miséricordieux.", "resource_id": 31},
            ],
        },
    ]
}

RECITATIONS_PAYLOAD = {
    "recitations": [
        {"id": 7, "name": "Mishary Alafasy", "style": "Alafasy", "relative_path": "Alafasy"},
        {"id": 126, "name": "Al-Afasy per verse", "style": "per_ayaah", "relative_path": "Alafasy_per_ayaah"},
    ]
}


@pytest.fixture(autouse=True)
def clean_cache():
    cache.clear()
    yield
    cache.clear()


class TestNormalization:
    def test_normalize_chapters(self):
        chapters = quran_client.normalize_chapters(CHAPTERS_PAYLOAD)
        assert len(chapters) == 2
        assert chapters[0] == {
            "number": 1,
            "name_arabic": "الفاتحة",
            "name_transliterated": "Al-Fatihah",
            "verses_count": 7,
            "revelation_place": "makkah",
        }

    def test_normalize_verses(self):
        verses = quran_client.normalize_verses(VERSES_PAYLOAD)
        assert verses[0]["ayah_number"] == 1
        assert verses[0]["text_uthmani"] == "بِسْمِ ٱللَّهِ ٱلرَّحْمَٰنِ ٱلرَّحِيمِ"
        assert verses[0]["translations"][0]["text"] == "Au nom d'Allah, le Tout Miséricordieux."

    def test_normalize_reciters_splits_chapter_and_verse(self):
        reciters = quran_client.normalize_reciters(RECITATIONS_PAYLOAD)
        assert [r["id"] for r in reciters["chapter"]] == [7]
        assert [r["id"] for r in reciters["verse"]] == [126]


class TestSurahEndpoints:
    SURAH_URL = "/api/v1/quran/surahs/"

    @responses.activate
    def test_surahs_public_and_cached(self, api_client):
        """L'endpoint est public ; le 2e appel ne rappelle pas Quran.com."""
        responses.add(
            responses.GET,
            f"{quran_client.settings.QURAN_API_BASE_URL}/chapters",
            json=CHAPTERS_PAYLOAD,
            status=200,
        )
        resp1 = api_client.get(self.SURAH_URL)
        assert resp1.status_code == 200
        assert len(resp1.data) == 2
        assert resp1.data[0]["name_transliterated"] == "Al-Fatihah"

        resp2 = api_client.get(self.SURAH_URL)
        assert resp2.status_code == 200
        assert len(responses.calls) == 1  # Quran.com appelé une seule fois

    @responses.activate
    def test_surahs_quran_down(self, api_client):
        responses.add(
            responses.GET,
            f"{quran_client.settings.QURAN_API_BASE_URL}/chapters",
            status=500,
        )
        resp = api_client.get(self.SURAH_URL)
        assert resp.status_code == 503
        assert resp.data["error"]["code"] == "external_api_error"


class TestVerseEndpoints:
    VERSES_URL = "/api/v1/quran/surahs/1/"

    @responses.activate
    def test_verses_with_translations(self, api_client):
        responses.add(
            responses.GET,
            f"{quran_client.settings.QURAN_API_BASE_URL}/verses/by_chapter/1",
            json=VERSES_PAYLOAD,
            status=200,
        )
        resp = api_client.get(self.VERSES_URL, {"translations": "fr,en"})
        assert resp.status_code == 200
        assert resp.data[0]["text_uthmani"].startswith("بِسْمِ")
        # Le code de langue est dérivé de la correspondance code -> resource_id
        # (l'API v4 ne renvoie pas de nom de langue dans les traductions).
        assert resp.data[0]["translations"][0]["code"] == "fr"
        assert resp.data[0]["translations"][0]["resource_id"] == 31

    def test_invalid_surah_number(self, api_client):
        resp = api_client.get("/api/v1/quran/surahs/200/")
        assert resp.status_code == 400
        assert resp.data["error"]["code"] == "invalid_params"


class TestAudioEndpoints:
    @responses.activate
    def test_chapter_audio(self, api_client):
        responses.add(
            responses.GET,
            f"{quran_client.settings.QURAN_API_BASE_URL}/chapter_recitations/7/2",
            json={"audio_file": {"audio_url": "https://download.quranicaudio.com/quran/2.mp3"}},
            status=200,
        )
        resp = api_client.get("/api/v1/quran/audio/chapter/2/", {"reciter_id": 7})
        assert resp.status_code == 200
        assert resp.data["audio_url"] == "https://download.quranicaudio.com/quran/2.mp3"

    @responses.activate
    def test_chapter_audio_with_timestamps(self, api_client):
        responses.add(
            responses.GET,
            f"{quran_client.settings.QURAN_API_BASE_URL}/chapter_recitations/7/1",
            json={"audio_file": {
                "audio_url": "https://download.quranicaudio.com/quran/1.mp3",
                "timestamps": [
                    {"verse_key": "1:1", "timestamp_from": 0, "timestamp_to": 5000,
                     "segments": [[1, 0, 900], [2, 900, 2000]]},
                    {"verse_key": "bad"},
                ],
            }},
            status=200,
        )
        resp = api_client.get("/api/v1/quran/audio/chapter/1/", {"reciter_id": 7})
        assert resp.status_code == 200
        assert resp.data["timestamps"] == [
            {"ayah": 1, "from": 0, "to": 5000, "segments": [[1, 0, 900], [2, 900, 2000]]}
        ]

    @responses.activate
    def test_verse_audio_with_timings(self, api_client):
        responses.add(
            responses.GET,
            f"{quran_client.settings.QURAN_API_BASE_URL}/recitations/7/by_ayah/2:255",
            json={"audio_files": [{"verse_key": "2:255",
                                   "url": "Alafasy/mp3/002255.mp3",
                                   "segments": [[1, 0, 1000]]}]},
            status=200,
        )
        resp = api_client.get("/api/v1/quran/audio/verse/", {"surah": 2, "ayah": 255, "reciter_id": 7})
        assert resp.status_code == 200
        assert resp.data["audio_url"] == "https://verses.quran.com/Alafasy/mp3/002255.mp3"
        assert resp.data["timings"]["segments"] == [[1, 0, 1000]]

    def test_verse_audio_invalid_params(self, api_client):
        resp = api_client.get("/api/v1/quran/audio/verse/", {"surah": "abc", "ayah": 1})
        assert resp.status_code == 400
        assert resp.data["error"]["code"] == "invalid_params"


class TestReadingProgress:
    PROGRESS_URL = "/api/v1/quran/progress/"

    def test_progress_requires_auth(self, api_client):
        resp = api_client.get(self.PROGRESS_URL)
        assert resp.status_code == 401
        assert resp.data["error"]["code"] == "unauthorized"

    def test_get_creates_default_progress(self, auth_client, user):
        resp = auth_client.get(self.PROGRESS_URL)
        assert resp.status_code == 200
        assert resp.data["last_surah_number"] is None

    def test_put_updates_progress(self, auth_client, user):
        resp = auth_client.put(
            self.PROGRESS_URL,
            {"last_surah_number": 2, "last_ayah_number": 255},
            format="json",
        )
        assert resp.status_code == 200
        assert resp.data["last_surah_number"] == 2
        assert resp.data["last_ayah_number"] == 255

    def test_put_invalid_surah(self, auth_client, user):
        resp = auth_client.put(
            self.PROGRESS_URL, {"last_surah_number": 999}, format="json"
        )
        assert resp.status_code == 400


class TestExtraReciters:
    @responses.activate
    def test_moroccan_reciters_listed(self, api_client):
        responses.add(
            responses.GET,
            f"{quran_client.settings.QURAN_API_BASE_URL}/resources/recitations",
            json=RECITATIONS_PAYLOAD, status=200,
        )
        resp = api_client.get("/api/v1/quran/reciters/")
        assert resp.status_code == 200
        names = [r["name"] for r in resp.data["chapter"]]
        assert "Omar Al-Qazabri" in names
        assert all("server" not in r for r in resp.data["chapter"])

    def test_extra_reciter_chapter_audio_without_quran_com(self, api_client):
        resp = api_client.get("/api/v1/quran/audio/chapter/2/", {"reciter_id": 100080})
        assert resp.status_code == 200
        assert resp.data["audio_url"] == "https://cdn.mp3quran.net/audio/omar-kazabri/r1/002.mp3"
