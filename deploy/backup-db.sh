#!/usr/bin/env bash
# =============================================================================
# Sauvegarde PostgreSQL de « Prière & Coran » (pg_dump compressé + rotation).
#
# Sauvegarde aussi le .env (clés VAPID, SECRET_KEY) : sans les clés VAPID, les
# abonnements push des utilisateurs deviennent inutilisables après une
# restauration sur un autre serveur.
#
# Usage manuel :   sudo /opt/salawat/deploy/backup-db.sh
# Cron (voir BACKUP.md) : tous les jours à 04:00.
#
# Variables surchargeables (valeurs par défaut pour la VPS Hostinger) :
#   APP_DIR        /opt/salawat
#   COMPOSE_FILES  "-f docker-compose.prod.yml -f docker-compose.vps.yml"
#   BACKUP_DIR     /var/backups/salawat
#   KEEP_DAYS      30
# =============================================================================
set -euo pipefail

APP_DIR="${APP_DIR:-/opt/salawat}"
COMPOSE_FILES="${COMPOSE_FILES:--f docker-compose.prod.yml -f docker-compose.vps.yml}"
BACKUP_DIR="${BACKUP_DIR:-/var/backups/salawat}"
KEEP_DAYS="${KEEP_DAYS:-30}"

umask 077
mkdir -p "$BACKUP_DIR"
cd "$APP_DIR"

# Millisecondes : deux sauvegardes la même seconde ne s'écrasent jamais.
STAMP="$(date +%Y%m%d-%H%M%S-%3N)"
OUT="$BACKUP_DIR/db-$STAMP.sql.gz"
TMP="$OUT.partial"

# Un seul sauvegarde à la fois.
exec 9>"$BACKUP_DIR/.lock"
flock -n 9 || { echo "Une sauvegarde est déjà en cours." >&2; exit 1; }

cleanup() { rm -f "$TMP"; }
trap cleanup EXIT

# --no-owner/--no-privileges : restauration possible vers un autre utilisateur.
# Identifiants lus DANS le conteneur (aucun mot de passe sur la ligne de commande).
# shellcheck disable=SC2086
docker compose $COMPOSE_FILES exec -T db \
  sh -c 'pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" --no-owner --no-privileges' \
  | gzip -9 > "$TMP"

# Contrôles : archive valide et non vide.
gzip -t "$TMP"
if [ "$(gzip -dc "$TMP" | wc -c)" -lt 1000 ]; then
  echo "Sauvegarde suspecte (trop petite) : abandon." >&2
  exit 1
fi
mv "$TMP" "$OUT"

# .env (secrets) : copie privée, un fichier par jour.
if [ -f "$APP_DIR/.env" ]; then
  cp "$APP_DIR/.env" "$BACKUP_DIR/env-$(date +%Y%m%d).bak"
fi

# Rotation.
find "$BACKUP_DIR" -name 'db-*.sql.gz' -mtime +"$KEEP_DAYS" -delete
find "$BACKUP_DIR" -name 'env-*.bak' -mtime +"$KEEP_DAYS" -delete

echo "OK $(basename "$OUT") ($(du -h "$OUT" | cut -f1)) — $(ls "$BACKUP_DIR"/db-*.sql.gz | wc -l) sauvegarde(s) conservée(s)"
