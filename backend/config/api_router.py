"""
Router central de l'API versionnée (/api/v1/).

Chaque app déclare ses propres URLs dans apps/<app>/urls.py ; elles sont
branchées ici. Les modules non encore implémentés restent commentés et
seront activés dans les étapes suivantes.
"""
from django.urls import include, path

api_urlpatterns = [
    path("auth/", include("apps.accounts.urls")),
    path("prayer-times/", include("apps.prayer_times.urls")),
    path("notifications/", include("apps.notifications.urls")),
    path("quran/", include("apps.quran.urls")),
    path("events/", include("apps.events.urls")),
    path("library/", include("apps.library.urls")),
    path("weather/", include("apps.weather.urls")),
    path("", include("apps.tools.urls")),
]
