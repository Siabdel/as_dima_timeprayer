"""
Paramètres communs aux environnements de développement et de production.

Toutes les valeurs sensibles proviennent de l'environnement : aucun secret
n'est écrit dans le code. Les fichiers dev.py et prod.py ajustent ensuite
les paramètres propres à chaque environnement.
"""
import os
from datetime import timedelta
from pathlib import Path

from kombu import Exchange, Queue

# BASE_DIR = backend/
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# ---------------------------------------------------------------------------
# Sécurité & secrets
# ---------------------------------------------------------------------------
SECRET_KEY = os.environ.get("SECRET_KEY")
if not SECRET_KEY:
    raise RuntimeError(
        "SECRET_KEY manquante : définissez-la dans l'environnement "
        "(voir .env.example)."
    )

DEBUG = False  # surchargé par dev.py / prod.py

ALLOWED_HOSTS: list[str] = []

# ---------------------------------------------------------------------------
# Applications
# ---------------------------------------------------------------------------
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # --- Tiers ---
    "rest_framework",
    "rest_framework_simplejwt",
    "rest_framework_simplejwt.token_blacklist",  # révocation des refresh tokens
    "corsheaders",
    # --- Applications du projet ---
    "apps.accounts",
    "apps.locations",
    "apps.prayer_times",
    "apps.quran",
    "apps.notifications",
    "apps.tools",
    "apps.events",
    "apps.library",
    "apps.weather",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",  # avant CommonMiddleware
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

# ---------------------------------------------------------------------------
# Base de données (PostgreSQL 16 ; basculée sur SQLite par dev.py hors Docker)
# ---------------------------------------------------------------------------
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ.get("POSTGRES_DB", "prayer_coran"),
        "USER": os.environ.get("POSTGRES_USER", "prayer"),
        "PASSWORD": os.environ.get("POSTGRES_PASSWORD", ""),
        "HOST": os.environ.get("DB_HOST", "localhost"),
        "PORT": os.environ.get("DB_PORT", "5432"),
    }
}

# ---------------------------------------------------------------------------
# Cache Redis (django-redis) — DB 0 dédiée au cache, séparée du broker Celery
# ---------------------------------------------------------------------------
REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": REDIS_URL,
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        },
        "KEY_PREFIX": "prayer_coran",
    }
}

# ---------------------------------------------------------------------------
# Authentification : utilisateur custom (e-mail comme identifiant)
# ---------------------------------------------------------------------------
AUTH_USER_MODEL = "accounts.User"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# ---------------------------------------------------------------------------
# DRF : JWT par défaut, permissions ouvertes par défaut (le Coran et les
# horaires sont publics), erreurs au format {"error": {...}}, throttles.
# ---------------------------------------------------------------------------
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.AllowAny",),
    "EXCEPTION_HANDLER": "config.exceptions.custom_exception_handler",
    "DEFAULT_THROTTLE_CLASSES": (
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ),
    "DEFAULT_THROTTLE_RATES": {
        # Appli publique de lecture : aperçus de récitateurs, versets, météo…
        # (100/h était atteint en quelques minutes). Surchargeable par env.
        "anon": os.environ.get("THROTTLE_ANON", "1500/hour"),
        "user": os.environ.get("THROTTLE_USER", "5000/hour"),
        "register": "5/hour",
        "notification_test": "10/hour",
    },
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 50,
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=30),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "AUTH_HEADER_TYPES": ("Bearer",),
}

# ---------------------------------------------------------------------------
# CORS : uniquement le domaine du frontend (variables d'environnement)
# ---------------------------------------------------------------------------
CORS_ALLOWED_ORIGINS = [
    o.strip()
    for o in os.environ.get(
        "CORS_ALLOWED_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173"
    ).split(",")
    if o.strip()
]
CORS_ALLOW_CREDENTIALS = True

# ---------------------------------------------------------------------------
# Internationalisation / fuseau horaire
# ---------------------------------------------------------------------------
LANGUAGE_CODE = "fr-fr"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# ---------------------------------------------------------------------------
# Fichiers statiques
# ---------------------------------------------------------------------------
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ---------------------------------------------------------------------------
# Celery : deux files pour isoler les notifications (critiques) du reste
# ---------------------------------------------------------------------------
CELERY_BROKER_URL = os.environ.get("CELERY_BROKER_URL", "redis://localhost:6379/1")
CELERY_RESULT_BACKEND = os.environ.get("CELERY_RESULT_BACKEND", "redis://localhost:6379/2")

CELERY_TASK_DEFAULT_QUEUE = "default"
CELERY_TASK_QUEUES = (
    Queue("default", Exchange("default"), routing_key="default"),
    Queue("notifications", Exchange("notifications"), routing_key="notifications"),
)
# Toutes les tâches de l'app notifications partent dans la file dédiée ;
# en production, un worker distinct peut n'écouter que cette file.
CELERY_TASK_ROUTES = {
    "apps.notifications.tasks.*": {"queue": "notifications"},
}

CELERY_TASK_ACKS_LATE = True
CELERY_WORKER_PREFETCH_MULTIPLIER = 1
# Les tâches eager (tests) ignorent le broker — activé via l'env dans conftest.
CELERY_TASK_ALWAYS_EAGER = os.environ.get("CELERY_TASK_ALWAYS_EAGER", "").lower() in ("1", "true")

# Le planificateur Celery Beat : le scanner des notifications s'exécute
# toutes les 5 minutes (fenêtre de déclenchement identique à SCAN_INTERVAL).
CELERY_BEAT_SCHEDULE = {
    "scan-prayer-notifications": {
        "task": "apps.notifications.tasks.scan_prayer_notifications",
        "schedule": 300.0,  # secondes
        "options": {"queue": "default"},
    },
}

# ---------------------------------------------------------------------------
# APIs externes — clés jamais exposées au frontend
# ---------------------------------------------------------------------------
ALADHAN_API_BASE_URL = os.environ.get("ALADHAN_API_BASE_URL", "https://api.aladhan.com/v1")

QURAN_API_BASE_URL = os.environ.get("QURAN_API_BASE_URL", "https://api.quran.com/api/v4")
QURAN_CLIENT_ID = os.environ.get("QURAN_CLIENT_ID", "")
QURAN_CLIENT_SECRET = os.environ.get("QURAN_CLIENT_SECRET", "")

# ---------------------------------------------------------------------------
# Web Push (VAPID) — la clé publique est servie par l'API (pas le secret)
# ---------------------------------------------------------------------------
VAPID_PUBLIC_KEY = os.environ.get("VAPID_PUBLIC_KEY", "")
VAPID_PRIVATE_KEY = os.environ.get("VAPID_PRIVATE_KEY", "")
VAPID_ADMIN_EMAIL = os.environ.get("VAPID_ADMIN_EMAIL", "")
