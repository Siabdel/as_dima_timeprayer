#!/usr/bin/env bash
# Sauvegarde du portail « dimatlas » (portail.dimatlas.com) : base PostgreSQL + volume
# des fichiers téléversés (mediafiles) + .env. Réutilise backup-db.sh.
# Projet Compose du portail : /home/django/dimatlas-portal (infra/docker-compose.prod.yml).
# Vérifiez le nom du volume : docker volume ls | grep mediafiles
export APP_DIR="${APP_DIR:-/home/django/dimatlas-portal}"
export COMPOSE_FILES="${COMPOSE_FILES:---env-file .env -f infra/docker-compose.prod.yml}"
export BACKUP_DIR="${BACKUP_DIR:-/var/backups/dimatlas}"
export MEDIA_VOLUME="${MEDIA_VOLUME:-dimatlas_mediafiles}"
exec "$(dirname "$0")/backup-db.sh" "$@"
