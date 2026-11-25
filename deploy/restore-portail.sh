#!/usr/bin/env bash
# Restauration de la BASE du portail « dimatlas » (remplace les données actuelles).
# Usage : sudo deploy/restore-portail.sh /var/backups/dimatlas/db-….sql.gz
# Les fichiers téléversés se restaurent séparément (voir BACKUP.md §7).
export APP_DIR="${APP_DIR:-/home/django/dimatlas-portal}"
export COMPOSE_FILES="${COMPOSE_FILES:---env-file .env -f infra/docker-compose.prod.yml}"
export BACKUP_DIR="${BACKUP_DIR:-/var/backups/dimatlas}"
export STOP_SERVICES="${STOP_SERVICES:-django celery celery_beat}"
# Pas de volume média dans la sauvegarde de sécurité automatique du restore.
export MEDIA_VOLUME=""
exec "$(dirname "$0")/restore-db.sh" "$@"
