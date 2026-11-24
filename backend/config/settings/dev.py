"""Paramètres de développement (Docker compose et tests locaux hors Docker)."""
import os

from .base import *  # noqa: F401,F403

DEBUG = os.environ.get("DEBUG", "True").lower() in ("1", "true")

ALLOWED_HOSTS = [
    h.strip()
    for h in os.environ.get(
        "DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1,backend"
    ).split(",")
    if h.strip()
]

# ---------------------------------------------------------------------------
# Environnement local sans Docker : SQLite + cache mémoire pour que `pytest`
# fonctionne sans services externes. En Docker, DB_HOST et REDIS_URL sont
# définis par docker-compose.yml et l'on garde PostgreSQL + Redis.
# ---------------------------------------------------------------------------
if os.environ.get("DB_HOST"):
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": os.environ.get("POSTGRES_DB", "prayer_coran"),
            "USER": os.environ.get("POSTGRES_USER", "prayer"),
            "PASSWORD": os.environ.get("POSTGRES_PASSWORD", ""),
            "HOST": os.environ["DB_HOST"],
            "PORT": os.environ.get("DB_PORT", "5432"),
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",  # noqa: F405
        }
    }

if not os.environ.get("REDIS_URL"):
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "prayer-coran-local-cache",
        }
    }

# ---------------------------------------------------------------------------
# En mode test (défini par conftest.py) :
#   * cache mémoire : les compteurs de throttle ne fuient pas dans Redis ni
#     entre deux exécutions de la suite de tests ;
#   * limites de débit relevées pour que les tests dépassent les quotas de
#     production (5/h sur l'inscription) — le throttling reste actif.
# ---------------------------------------------------------------------------
if os.environ.get("TESTING", "").lower() in ("1", "true"):
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "prayer-coran-test-cache",
        }
    }

# En développement local, les tests E2E (Playwright) créent ~10 comptes par
# exécution de la suite : le quota de production (5/h) les bloquerait en 429.
# On relève le taux de l'inscription en dev (la prod garde 5/h via base.py).
REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"] = {
    **REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"],  # noqa: F405
    "register": "1000/hour",
    "notification_test": "1000/hour",
}
