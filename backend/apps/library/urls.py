"""URLs de l'app library (montées sous /api/v1/library/)."""
from django.urls import path

from .views import DuaListView, HadithListView, LibraryCategoriesView

urlpatterns = [
    path("duas/", DuaListView.as_view(), name="library-duas"),
    path("hadiths/", HadithListView.as_view(), name="library-hadiths"),
    path("categories/", LibraryCategoriesView.as_view(), name="library-categories"),
]
