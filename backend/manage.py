#!/usr/bin/env python
"""Utilitaire en ligne de commande Django pour le projet Prière & Coran."""
import os
import sys


def main() -> None:
    # Le compose de développement utilise config.settings.dev ; la production
    # passe DJANGO_SETTINGS_MODULE=config.settings.prod via l'environnement.
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Django est introuvable. Avez-vous activé votre environnement "
            "virtuel et installé les dépendances ?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
