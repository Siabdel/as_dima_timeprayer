"""Serializers de l'app quran."""
from rest_framework import serializers


class SurahSerializer(serializers.Serializer):
    """Une sourate : numéro, nom arabe, translittération, versets, lieu."""

    number = serializers.IntegerField()
    name_arabic = serializers.CharField()
    name_transliterated = serializers.CharField()
    verses_count = serializers.IntegerField()
    revelation_place = serializers.CharField()


class VerseTranslationSerializer(serializers.Serializer):
    code = serializers.CharField()
    text = serializers.CharField()
    resource_id = serializers.IntegerField()


class VerseSerializer(serializers.Serializer):
    """Un verset : numéro, texte Uthmani, traductions demandées."""

    ayah_number = serializers.IntegerField()
    text_uthmani = serializers.CharField()
    translations = VerseTranslationSerializer(many=True)


class QuranWordSerializer(serializers.Serializer):
    """Un mot coranique pour la lecture mot à mot (Word-by-Word)."""

    position = serializers.IntegerField()
    text_uthmani = serializers.CharField()
    translation_fr = serializers.CharField(allow_blank=True)
    translation_en = serializers.CharField(allow_blank=True)
    transliteration = serializers.CharField(allow_blank=True)
    audio_url = serializers.CharField(allow_blank=True)
    is_end = serializers.BooleanField()


class VerseWordsSerializer(serializers.Serializer):
    """Mots d'un verset (endpoint unitaire /quran/words/{s}/{a}/)."""

    verse_key = serializers.CharField()
    words = QuranWordSerializer(many=True)


class ChapterVerseWordsSerializer(serializers.Serializer):
    """Mots d'un verset dans la réponse d'une sourate entière."""

    ayah_number = serializers.IntegerField()
    verse_key = serializers.CharField()
    words = QuranWordSerializer(many=True)


class ChapterAudioSerializer(serializers.Serializer):
    """URL audio d'une sourate complète + horodatages (ms) par verset/mot."""

    audio_url = serializers.URLField()
    timestamps = serializers.ListField(
        child=serializers.DictField(child=serializers.JSONField()),
        required=False,
    )


class VerseAudioSerializer(serializers.Serializer):
    """URL audio d'un verset + timings (segments) si disponibles."""

    audio_url = serializers.URLField()
    timings = serializers.DictField(child=serializers.JSONField(), required=False)


class ReadingProgressSerializer(serializers.Serializer):
    """Progression de lecture de l'utilisateur authentifié."""

    last_surah_number = serializers.IntegerField(min_value=1, max_value=114, allow_null=True)
    last_ayah_number = serializers.IntegerField(min_value=1, max_value=286, allow_null=True)
    updated_at = serializers.DateTimeField(read_only=True)

    def create(self, validated_data):
        from .models import ReadingProgress

        return ReadingProgress.objects.create(**validated_data)

    def update(self, instance, validated_data):
        instance.last_surah_number = validated_data.get("last_surah_number", instance.last_surah_number)
        instance.last_ayah_number = validated_data.get("last_ayah_number", instance.last_ayah_number)
        instance.save()
        return instance
