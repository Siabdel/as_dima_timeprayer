"""Paramètres de production : stricts et en échec rapide si mal configurés."""
import os

from django.core.exceptions import ImproperlyConfigured

from .base import *  # noqa: F401,F403

DEBUG = False

if not SECRET_KEY or SECRET_KEY.startswith("test-"):
    raise ImproperlyConfigured(
        "SECRET_KEY doit être défini avec une valeur forte en production."
    )

ALLOWED_HOSTS = [
    h.strip()
    for h in os.environ.get("DJANGO_ALLOWED_HOSTS", "").split(",")
    if h.strip()
]
if not ALLOWED_HOSTS:
    raise ImproperlyConfigured(
        "DJANGO_ALLOWED_HOSTS doit être défini en production (domaine backend)."
    )

# ---------------------------------------------------------------------------
# PostgreSQL obligatoire en production
# ---------------------------------------------------------------------------
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ.get("POSTGRES_DB", "prayer_coran"),
        "USER": os.environ.get("POSTGRES_USER", "prayer"),
        "PASSWORD": os.environ.get("POSTGRES_PASSWORD", ""),
        "HOST": os.environ.get("DB_HOST", "db"),
        "PORT": os.environ.get("DB_PORT", "5432"),
    }
}

# ---------------------------------------------------------------------------
# Redis obligatoire en production
# ---------------------------------------------------------------------------
if not os.environ.get("REDIS_URL"):
    raise ImproperlyConfigured("REDIS_URL doit être défini en production.")

# ---------------------------------------------------------------------------
# Endoss HTTPS (nginx / reverse proxy TLS en amont)
# ---------------------------------------------------------------------------
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = os.environ.get("SECURE_SSL_REDIRECT", "true").lower() == "true"
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# CSRF : nécessaire derrière un reverse proxy TLS (admin Django, POST).
# Défaut : le domaine du frontend (FRONTEND_URL) ; extensible via
# CSRF_TRUSTED_ORIGINS="https://a.exemple.com,https://b.exemple.com".
_csrf_origins = [
    o.strip()
    for o in os.environ.get("CSRF_TRUSTED_ORIGINS", "").split(",")
    if o.strip()
]
frontend_url = os.environ.get("FRONTEND_URL", "").rstrip("/")
if frontend_url and frontend_url not in _csrf_origins:
    _csrf_origins.append(frontend_url)
CSRF_TRUSTED_ORIGINS = _csrf_origins
