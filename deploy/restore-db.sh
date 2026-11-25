#!/usr/bin/env bash
# =============================================================================
# Restauration PostgreSQL de « Prière & Coran » depuis une sauvegarde .sql.gz.
#
# ATTENTION : remplace TOUTES les données actuelles de la base.
# Usage :  sudo /opt/salawat/deploy/restore-db.sh /var/backups/salawat/db-AAAAMMJJ-HHMMSS.sql.gz
# Le script crée d'abord une sauvegarde de sécurité de l'état actuel.
# =============================================================================
set -euo pipefail

APP_DIR="${APP_DIR:-/opt/salawat}"
COMPOSE_FILES="${COMPOSE_FILES:--f docker-compose.prod.yml -f docker-compose.vps.yml}"
BACKUP_DIR="${BACKUP_DIR:-/var/backups/salawat}"
# Services à arrêter pendant l'import (noms Compose) ; surchargeable.
STOP_SERVICES="${STOP_SERVICES:-backend worker worker-default beat}"
FILE="${1:-}"

[ -n "$FILE" ] && [ -f "$FILE" ] || { echo "Usage : $0 <sauvegarde.sql.gz>" >&2; exit 1; }
gzip -t "$FILE"

cd "$APP_DIR"
DC="docker compose $COMPOSE_FILES"

echo "Restauration de : $FILE"
echo "Cela REMPLACE toutes les données actuelles de la base."
if [ "${ASSUME_YES:-}" != "1" ]; then
  read -r -p "Tapez RESTAURER pour confirmer : " answer
  [ "$answer" = "RESTAURER" ] || { echo "Annulé."; exit 1; }
fi

echo "1/4 Sauvegarde de sécurité de l'état actuel…"
BACKUP_DIR="$BACKUP_DIR" APP_DIR="$APP_DIR" COMPOSE_FILES="$COMPOSE_FILES" "$(dirname "$0")/backup-db.sh"

echo "2/4 Arrêt des services qui utilisent la base…"
# shellcheck disable=SC2086
$DC stop $STOP_SERVICES >/dev/null 2>&1 || true

echo "3/4 Recréation du schéma et import…"
$DC exec -T db sh -c 'psql -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"' >/dev/null
gzip -dc "$FILE" | $DC exec -T db sh -c 'psql -v ON_ERROR_STOP=1 -q -U "$POSTGRES_USER" -d "$POSTGRES_DB"' >/dev/null

echo "4/4 Redémarrage…"
$DC up -d >/dev/null
echo "Restauration terminée."
