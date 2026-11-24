"""Administration du cahier de douâas et hadiths."""
from django.contrib import admin

from .models import Dua, Hadith


@admin.register(Dua)
class DuaAdmin(admin.ModelAdmin):
    list_display = ("title", "category", "source", "order")
    list_filter = ("category",)
    search_fields = ("title", "text_ar", "translation_fr", "source")


@admin.register(Hadith)
class HadithAdmin(admin.ModelAdmin):
    list_display = ("title", "category", "narrator", "source", "order")
    list_filter = ("category",)
    search_fields = ("title", "text_ar", "translation_fr", "source")
