"""Serializers de l'app prayer_times."""
from rest_framework import serializers


class HijriDateSerializer(serializers.Serializer):
    """Bloc date hégirien normalisé."""

    date = serializers.CharField()
    day = serializers.CharField()
    year = serializers.CharField()
    month = serializers.DictField(child=serializers.CharField(allow_null=True))


class PrayerTimesSerializer(serializers.Serializer):
    """
    Format interne stable des horaires :
    {fajr, sunrise, dhuhr, asr, maghrib, isha, hijri_date, timezone}
    + métadonnées (location, date, method, madhhab, stale).
    """

    fajr = serializers.CharField()
    sunrise = serializers.CharField()
    dhuhr = serializers.CharField()
    asr = serializers.CharField()
    maghrib = serializers.CharField()
    isha = serializers.CharField()
    hijri_date = HijriDateSerializer()
    timezone = serializers.CharField()

    # Métadonnées ajoutées par la vue
    location = serializers.DictField()
    date = serializers.CharField()
    method = serializers.IntegerField()
    madhhab = serializers.CharField()
    stale = serializers.BooleanField(default=False)
