"""
Vues de l'app library :
- GET /api/v1/library/duas/     → liste des douâas (filtre ?category=)
- GET /api/v1/library/hadiths/  → liste des hadiths (filtre ?category=)
- GET /api/v1/library/categories/ → catégories des deux (public)
"""
from rest_framework import generics, permissions
from rest_framework.response import Response

from .models import Dua, Hadith
from .serializers import (
    DUA_CATEGORY_LABELS,
    HADITH_CATEGORY_LABELS,
    DuaSerializer,
    HadithSerializer,
)


class DuaListView(generics.ListAPIView):
    """Douâas du cahier — optionnellement filtrées par catégorie."""

    serializer_class = DuaSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        queryset = Dua.objects.all()
        category = self.request.query_params.get("category")
        if category:
            queryset = queryset.filter(category=category)
        return queryset


class HadithListView(generics.ListAPIView):
    """Hadiths du Prophète ﷺ — optionnellement filtrés par catégorie."""

    serializer_class = HadithSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        queryset = Hadith.objects.all()
        category = self.request.query_params.get("category")
        if category:
            queryset = queryset.filter(category=category)
        return queryset


class LibraryCategoriesView(generics.ListAPIView):
    """
    Catégories disponibles (douâas + hadiths) avec leur libellé français —
    permet au frontend de construire ses onglets sans hardcoder.
    """

    permission_classes = [permissions.AllowAny]

    def list(self, request, *args, **kwargs):
        return Response(
            {
                "duas": [
                    {"key": key, "label": label}
                    for key, label in DUA_CATEGORY_LABELS.items()
                ],
                "hadiths": [
                    {"key": key, "label": label}
                    for key, label in HADITH_CATEGORY_LABELS.items()
                ],
            }
        )
