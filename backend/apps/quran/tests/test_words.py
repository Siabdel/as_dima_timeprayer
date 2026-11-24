"""
Tests de la lecture mot à mot (Word-by-Word) :
- lexique français (normalisation arabe, traductions connues)
- normalisation des mots Quran.com
- endpoints /quran/words/{surah}/{ayah}/ et /quran/surahs/{n}/?words=true
"""
import pytest
import responses
from django.core.cache import cache

from apps.quran.services import quran_client
from apps.quran.services.lexicon_fr import normalize_arabic, translate_word

pytestmark = pytest.mark.django_db

# Payload Quran.com simplifié avec mots (structure réelle)
WORDS_PAYLOAD = {
    "verse": {
        "verse_key": "1:1",
        "words": [
            {
                "id": 1, "position": 1, "char_type_name": "word",
                "text_uthmani": "بِسْمِ",
                "audio_url": "wbw/001_001_001.mp3",
                "translation": {"text": "In (the) name", "language_name": "english"},
                "transliteration": {"text": "bis'mi"},
            },
            {
                "id": 2, "position": 2, "char_type_name": "word",
                "text_uthmani": "ٱللَّهِ",
                "audio_url": "wbw/001_001_002.mp3",
                "translation": {"text": "(of) Allah", "language_name": "english"},
                "transliteration": {"text": "l-lahi"},
            },
            {
                "id": 3, "position": 3, "char_type_name": "end",
                "text_uthmani": "١",
                "audio_url": "",
                "translation": {"text": "(1)"},
                "transliteration": {"text": ""},
            },
        ],
    }
}

CHAPTER_WORDS_PAYLOAD = {
    "verses": [
        {
            "verse_number": 1,
            "verse_key": "1:1",
            "text_uthmani": "بِسْمِ ٱللَّهِ",
            "words": WORDS_PAYLOAD["verse"]["words"],
        }
    ]
}

CHAPTER_VERSES_PAYLOAD = {
    "verses": [
        {
            "verse_number": 1,
            "verse_key": "1:1",
            "text_uthmani": "بِسْمِ ٱللَّهِ",
            "translations": [
                {"language_name": "french", "text": "Au nom d'Allah", "resource_id": 31}
            ],
        }
    ]
}


@pytest.fixture(autouse=True)
def clean_cache():
    cache.clear()
    yield
    cache.clear()


class TestFrenchLexicon:
    def test_normalize_removes_diacritics(self):
        assert normalize_arabic("بِسْمِ") == "بسم"
        assert normalize_arabic("ٱللَّهِ") == "الله"
        assert normalize_arabic("ٱلرَّحْمَـٰنِ") == "الرحمن"

    def test_normalize_alif_variants(self):
        # Toutes les formes d'alif convergent vers la même clé.
        assert normalize_arabic("ٱلْحَمْدُ") == normalize_arabic("الحمد")

    def test_known_words_translated(self):
        assert translate_word("بِسْمِ") == "au nom de"
        assert translate_word("ٱللَّهِ") == "Allah"
        assert translate_word("ٱلرَّحْمَـٰنِ") == "le Tout Miséricordieux"

    def test_unknown_word_returns_none(self):
        assert translate_word("كلمة_غريبة_غير_موجودة") is None
        assert translate_word("") is None


class TestNormalizeWords:
    def test_normalize_words_structure(self):
        words = quran_client.normalize_words(WORDS_PAYLOAD["verse"])
        assert len(words) == 3

        first = words[0]
        assert first["position"] == 1
        assert first["text_uthmani"] == "بِسْمِ"
        # Traduction FR depuis le lexique local
        assert first["translation_fr"] == "au nom de"
        # Traduction anglaise conservée en secours
        assert first["translation_en"] == "In (the) name"
        assert first["transliteration"] == "bis'mi"
        assert first["audio_url"] == "https://verses.quran.com/wbw/001_001_001.mp3"
        assert first["is_end"] is False

        # Marqueur de fin de verset
        assert words[2]["is_end"] is True

    def test_unknown_word_falls_back_to_english(self):
        words = quran_client.normalize_words(
            {"words": [{
                "position": 1, "char_type_name": "word",
                "text_uthmani": "زَخْرَفَةٌ", "audio_url": "",
                "translation": {"text": "ornament"},
            }]}
        )
        # Mot absent du lexique → traduction anglaise en repli
        assert words[0]["translation_fr"] == "ornament"


class TestWordsEndpoints:
    WORDS_URL = "/api/v1/quran/words/1/1/"

    @responses.activate
    def test_verse_words_public(self, api_client):
        responses.add(
            responses.GET,
            f"{quran_client.settings.QURAN_API_BASE_URL}/verses/by_key/1:1",
            json=WORDS_PAYLOAD, status=200,
        )
        resp = api_client.get(self.WORDS_URL)
        assert resp.status_code == 200, resp.data
        assert resp.data["verse_key"] == "1:1"
        assert len(resp.data["words"]) == 3
        assert resp.data["words"][0]["translation_fr"] == "au nom de"

    @responses.activate
    def test_verse_words_cached(self, api_client):
        responses.add(
            responses.GET,
            f"{quran_client.settings.QURAN_API_BASE_URL}/verses/by_key/1:1",
            json=WORDS_PAYLOAD, status=200,
        )
        api_client.get(self.WORDS_URL)
        api_client.get(self.WORDS_URL)
        assert len(responses.calls) == 1  # Quran.com appelé une seule fois

    def test_invalid_params(self, api_client):
        resp = api_client.get("/api/v1/quran/words/999/1/")
        assert resp.status_code == 400
        assert resp.data["error"]["code"] == "invalid_params"

    @responses.activate
    def test_surah_with_words_param(self, api_client):
        """?words=true ajoute les mots à chaque verset de la sourate."""
        responses.add(
            responses.GET,
            f"{quran_client.settings.QURAN_API_BASE_URL}/verses/by_chapter/1",
            json=CHAPTER_WORDS_PAYLOAD, status=200,
        )
        resp = api_client.get("/api/v1/quran/surahs/1/", {"words": "true"})
        assert resp.status_code == 200, resp.data
        assert "words" in resp.data[0]
        assert len(resp.data[0]["words"]) == 3