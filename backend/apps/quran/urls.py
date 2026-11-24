"""URLs de l'app quran (montées sous /api/v1/quran/)."""
from django.urls import path

from .views import (
    ChapterAudioView,
    ReadingProgressView,
    RecitersView,
    SurahDetailView,
    SurahListView,
    VerseAudioView,
    VerseWordsView,
)

urlpatterns = [
    path("surahs/", SurahListView.as_view(), name="surah-list"),
    path("surahs/<int:number>/", SurahDetailView.as_view(), name="surah-detail"),
    path("reciters/", RecitersView.as_view(), name="reciters"),
    path("audio/chapter/<int:surah>/", ChapterAudioView.as_view(), name="chapter-audio"),
    path("audio/verse/", VerseAudioView.as_view(), name="verse-audio"),
    # Lecture mot à mot : mots d'un verset isolé
    path("words/<int:surah>/<int:ayah>/", VerseWordsView.as_view(), name="verse-words"),
    path("progress/", ReadingProgressView.as_view(), name="reading-progress"),
]