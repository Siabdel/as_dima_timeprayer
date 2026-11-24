"""
Vues de l'app quran — accessibles SANS authentification pour la lecture
(cahier des charges), JWT requis uniquement pour la progression de lecture.

Endpoints :
- GET    /api/v1/quran/surahs/                   → liste des 114 sourates
- GET    /api/v1/quran/surahs/{number}/          → versets + traductions
- GET    /api/v1/quran/reciters/                 → récitateurs (chapitre/verset)
- GET    /api/v1/quran/audio/chapter/{surah}/    → URL audio sourate
- GET    /api/v1/quran/audio/verse/              → URL audio verset + timings
- GET/PUT /api/v1/quran/progress/                → progression (JWT)
"""
import logging

from django.core.cache import cache
from django.shortcuts import get_object_or_404
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import ReadingProgress
from .serializers import (
    ChapterAudioSerializer,
    ReadingProgressSerializer,
    SurahSerializer,
    VerseAudioSerializer,
    VerseSerializer,
    VerseWordsSerializer,
)
from .services import quran_client

logger = logging.getLogger(__name__)

CACHE_TTL = 60 * 60 * 24  # texte statique : 24 h suffisent


def _error_response(code: str, message: str, http_status: int) -> Response:
    """Format d'erreur uniforme {"error": {code, message}}."""
    return Response({"error": {"code": code, "message": message}}, status=http_status)


def _cached(key: str, fetcher):
    """Lit le cache ; sinon appelle Quran.com puis met en cache (jamais 2 appels)."""
    cached = cache.get(key)
    if cached is not None:
        return cached
    try:
        data = fetcher()
    except quran_client.QuranAPIError as exc:
        raise QuranUnavailableError(str(exc)) from exc
    cache.set(key, data, timeout=CACHE_TTL)
    return data


class QuranUnavailableError(Exception):
    """Quran.com indisponible (proxy de l'erreur client vers la couche vue)."""


class SurahListView(APIView):
    """GET /api/v1/quran/surahs/ — liste des 114 sourates."""

    permission_classes = [permissions.AllowAny]

    def get(self, request):
        try:
            surahs = _cached("quran:surahs", quran_client.fetch_surahs)
        except QuranUnavailableError as exc:
            return _error_response(
                "external_api_error", str(exc), status.HTTP_503_SERVICE_UNAVAILABLE
            )
        return Response(SurahSerializer(surahs, many=True).data)


class SurahDetailView(APIView):
    """GET /api/v1/quran/surahs/{number}/?translations=fr,en"""

    permission_classes = [permissions.AllowAny]

    def get(self, request, number: int):
        if not 1 <= number <= 114:
            return _error_response(
                "invalid_params", "Le numéro de sourate doit être entre 1 et 114.",
                status.HTTP_400_BAD_REQUEST,
            )
        translations_param = request.query_params.get("translations", "fr")
        translations = [
            t.strip() for t in translations_param.split(",") if t.strip()
        ][:5]  # max 5 traductions par requête
        # Mode mot à mot (?words=true) : la réponse inclut les `words` de
        # chaque verset (texte + traduction FR mot à mot + audio isolé).
        include_words = request.query_params.get("words", "").lower() in ("1", "true", "yes")

        if include_words:
            try:
                verses_words = _cached(
                    f"quran:chapter-words:{number}",
                    lambda: quran_client.fetch_chapter_words(number),
                )
                verses = _cached(
                    f"quran:verses:{number}:{','.join(sorted(translations))}",
                    lambda: quran_client.fetch_verses(number, translations),
                )
            except QuranUnavailableError as exc:
                return _error_response(
                    "external_api_error", str(exc), status.HTTP_503_SERVICE_UNAVAILABLE
                )
            # Fusion : chaque verset reçoit ses mots (même numéro de verset).
            words_by_ayah = {v["ayah_number"]: v["words"] for v in verses_words}
            payload = [
                {
                    "ayah_number": v["ayah_number"],
                    "text_uthmani": v["text_uthmani"],
                    "translations": v["translations"],
                    "words": words_by_ayah.get(v["ayah_number"], []),
                }
                for v in verses
            ]
            return Response(payload)

        try:
            verses = _cached(
                f"quran:verses:{number}:{','.join(sorted(translations))}",
                lambda: quran_client.fetch_verses(number, translations),
            )
        except QuranUnavailableError as exc:
            return _error_response(
                "external_api_error", str(exc), status.HTTP_503_SERVICE_UNAVAILABLE
            )
        return Response(VerseSerializer(verses, many=True).data)


class VerseWordsView(APIView):
    """GET /api/v1/quran/words/{surah}/{ayah}/ — mots d'un verset (public)."""

    permission_classes = [permissions.AllowAny]

    def get(self, request, surah: int, ayah: int):
        if not 1 <= surah <= 114 or ayah < 1:
            return _error_response(
                "invalid_params", "Numéro de sourate ou de verset invalide.",
                status.HTTP_400_BAD_REQUEST,
            )
        try:
            data = _cached(
                f"quran:words:{surah}:{ayah}",
                lambda: quran_client.fetch_verse_words(surah, ayah),
            )
        except QuranUnavailableError as exc:
            return _error_response(
                "external_api_error", str(exc), status.HTTP_503_SERVICE_UNAVAILABLE
            )
        return Response(VerseWordsSerializer(data).data)


class RecitersView(APIView):
    """GET /api/v1/quran/reciters/ — séparés chapitre / verset."""

    permission_classes = [permissions.AllowAny]

    def get(self, request):
        try:
            reciters = _cached("quran:reciters", quran_client.fetch_reciters)
        except QuranUnavailableError as exc:
            return _error_response(
                "external_api_error", str(exc), status.HTTP_503_SERVICE_UNAVAILABLE
            )
        # Récitateurs marocains ajoutés hors cache (liste statique).
        return Response({
            **reciters,
            "chapter": [*reciters.get("chapter", []), *quran_client.extra_reciters_public()],
        })


class ChapterAudioView(APIView):
    """GET /api/v1/quran/audio/chapter/{surah}/?reciter_id=7"""

    permission_classes = [permissions.AllowAny]

    def get(self, request, surah: int):
        if not 1 <= surah <= 114:
            return _error_response(
                "invalid_params", "Le numéro de sourate doit être entre 1 et 114.",
                status.HTTP_400_BAD_REQUEST,
            )
        # reciter_id : numérique (Quran.com / CDN externe) OU texte pour les
        # récitateurs hébergés localement (ex. « benmoussa »).
        raw_reciter = request.query_params.get("reciter_id", "7")
        reciter_id = raw_reciter.strip()
        if not reciter_id:
            reciter_id = "7"
        if reciter_id.isdigit():
            reciter_id = int(reciter_id)
        else:
            # Identifiant texte : doit correspondre à un récitateur local connu.
            from .local_reciters import get_local_reciter

            if get_local_reciter(reciter_id) is None:
                return _error_response(
                    "invalid_params",
                    "reciter_id inconnu : utilisez un identifiant numérique "
                    "ou un récitateur local de la liste /quran/reciters/.",
                    status.HTTP_400_BAD_REQUEST,
                )
        try:
            audio = quran_client.fetch_chapter_audio(surah, reciter_id)
        except quran_client.QuranAPIError as exc:
            return _error_response(
                "external_api_error", str(exc), status.HTTP_503_SERVICE_UNAVAILABLE
            )
        return Response(ChapterAudioSerializer(audio).data)


class VerseAudioView(APIView):
    """GET /api/v1/quran/audio/verse/?surah=2&ayah=255&reciter_id=7"""

    permission_classes = [permissions.AllowAny]

    def get(self, request):
        try:
            surah = int(request.query_params.get("surah", 0))
            ayah = int(request.query_params.get("ayah", 0))
            reciter_id = int(request.query_params.get("reciter_id", 7))
        except ValueError:
            return _error_response(
                "invalid_params", "surah, ayah et reciter_id doivent être des entiers.",
                status.HTTP_400_BAD_REQUEST,
            )
        if not 1 <= surah <= 114 or ayah < 1:
            return _error_response(
                "invalid_params", "Numéro de sourate ou de verset invalide.",
                status.HTTP_400_BAD_REQUEST,
            )
        try:
            audio = quran_client.fetch_verse_audio(surah, ayah, reciter_id)
        except quran_client.QuranAPIError as exc:
            return _error_response(
                "external_api_error", str(exc), status.HTTP_503_SERVICE_UNAVAILABLE
            )
        return Response(VerseAudioSerializer(audio).data)


class ReadingProgressView(APIView):
    """GET/PUT /api/v1/quran/progress/ — progression de lecture (JWT requis)."""

    permission_classes = [permissions.IsAuthenticated]

    def get_object(self) -> ReadingProgress:
        obj, _ = ReadingProgress.objects.get_or_create(user=self.request.user)
        return obj

    def get(self, request):
        serializer = ReadingProgressSerializer(self.get_object())
        return Response(serializer.data)

    def put(self, request):
        progress = self.get_object()
        serializer = ReadingProgressSerializer(progress, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)
