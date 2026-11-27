"""
Administration du texte du Coran (consultation seule).

Le texte coranique ne doit jamais être modifié à la main : il est chargé par
`python manage.py import_quran_text`. L'admin sert à le consulter et à
vérifier l'import ; ajout, modification et suppression y sont désactivés.
"""
from django.contrib import admin

from .models import Surah, Verse, VerseTranslation


class ReadOnlyAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


class VerseTranslationInline(admin.TabularInline):
    model = VerseTranslation
    extra = 0
    can_delete = False
    readonly_fields = ("code", "resource_id", "text")

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(Surah)
class SurahAdmin(ReadOnlyAdmin):
    list_display = ("number", "name_transliterated", "name_arabic", "verses_count", "revelation_place")
    list_filter = ("revelation_place",)
    search_fields = ("name_transliterated", "name_arabic")
    ordering = ("number",)


@admin.register(Verse)
class VerseAdmin(ReadOnlyAdmin):
    list_display = ("__str__", "surah", "ayah_number", "text_uthmani")
    list_filter = ("surah",)
    search_fields = ("text_uthmani", "translations__text")
    list_select_related = ("surah",)
    ordering = ("surah_id", "ayah_number")
    inlines = [VerseTranslationInline]


@admin.register(VerseTranslation)
class VerseTranslationAdmin(ReadOnlyAdmin):
    list_display = ("verse", "code", "resource_id", "text")
    list_filter = ("code", "verse__surah")
    search_fields = ("text",)
    list_select_related = ("verse",)
