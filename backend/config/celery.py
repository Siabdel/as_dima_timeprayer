"""Configuration de l'application Celery du projet."""
import os

from celery import Celery

# Valeur par défaut pour le développement local ; la production définit la
# variable d'environnement DJANGO_SETTINGS_MODULE elle-même (voir compose).
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")

app = Celery("prayer_coran")

# Toute la configuration CELERY_* est lue depuis les settings Django
# (namespace "CELERY" : ex. CELERY_BROKER_URL -> broker_url).
app.config_from_object("django.conf:settings", namespace="CELERY")

# Découvre automatiquement les tâches déclarées dans apps/*/tasks.py.
app.autodiscover_tasks()
