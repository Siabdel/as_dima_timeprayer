"""
Paquet de configuration du projet "Prière & Coran".

Importe l'application Celery afin que `@shared_task` et l'autodiscovery
fonctionnent dès le chargement de Django.
"""
from .celery import app as celery_app

__all__ = ("celery_app",)
