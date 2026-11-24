"""
Fixtures pytest partagées.

Les variables d'environnement de test sont définies AVANT l'import des
settings Django (pytest-django initialise Django après le chargement du
conftest racine). Sans REDIS_URL ni DB_HOST, les settings dev basculent
automatiquement sur un cache mémoire + SQLite : les tests tournent donc
sans Docker ni services externes.
"""
import os

os.environ.setdefault("SECRET_KEY", "test-secret-key-not-for-production")
os.environ.setdefault("DEBUG", "True")
os.environ.setdefault("TESTING", "1")
# Les tâches Celery s'exécutent de façon synchrone (eager) pendant les tests.
os.environ.setdefault("CELERY_TASK_ALWAYS_EAGER", "1")

import pytest  # noqa: E402
from rest_framework.test import APIClient  # noqa: E402

from apps.accounts.models import User, UserPreference  # noqa: E402


@pytest.fixture
def user(db) -> User:
    """Utilisateur de test avec un mot de passe conforme aux validateurs."""
    return User.objects.create_user(
        email="test@example.com",
        password="UnMotDePasseSolide1!",
        first_name="Test",
        last_name="Utilisateur",
    )


@pytest.fixture
def preference(user) -> UserPreference:
    """Préférence par défaut créée pour l'utilisateur de test."""
    obj, _ = UserPreference.objects.get_or_create(user=user)
    return obj


@pytest.fixture
def api_client() -> APIClient:
    return APIClient()


@pytest.fixture
def auth_client(api_client, user) -> APIClient:
    """Client HTTP déjà authentifié auprès du backend."""
    api_client.force_authenticate(user=user)
    return api_client
