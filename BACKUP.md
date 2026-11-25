# Sauvegarde et restauration de la base — Prière & Coran

Sauvegarde quotidienne de PostgreSQL sur la VPS Hostinger (`salawat.dimatlas.com`),
avec rotation, vérification d'intégrité et restauration guidée.

| Élément | Valeur |
|---|---|
| Scripts | `deploy/backup-db.sh`, `deploy/restore-db.sh` |
| Dossier des sauvegardes | `/var/backups/salawat/` (accessible à `root` seulement) |
| Fichiers | `db-AAAAMMJJ-HHMMSS-mmm.sql.gz` (base) et `env-AAAAMMJJ.bak` (secrets) |
| Fréquence / rétention | tous les jours à 04:00 / 30 jours (`KEEP_DAYS`) |
| Contenu de la base | comptes, préférences, abonnements push, progression de lecture, journaux de notifications |

> **Pourquoi sauvegarder aussi le `.env` ?** Il contient les clés **VAPID**. Si elles
> sont perdues, toutes les inscriptions aux notifications deviennent inutilisables
> (les utilisateurs doivent se réabonner). Il contient aussi `SECRET_KEY`.

## 1. Installation (une seule fois, sur la VPS)

Depuis votre ordinateur, copiez les scripts (le dossier du projet est à jour dans ce dépôt) :

```bash
scp deploy/backup-db.sh deploy/restore-db.sh root@187.124.184.110:/opt/salawat/deploy/
```

Sur la VPS :

```bash
chmod 700 /opt/salawat/deploy/backup-db.sh /opt/salawat/deploy/restore-db.sh
mkdir -p /var/backups/salawat && chmod 700 /var/backups/salawat

# 1) Essai manuel
/opt/salawat/deploy/backup-db.sh
ls -lh /var/backups/salawat/

# 2) Planification quotidienne (04:00) avec journal
cat > /etc/cron.d/salawat-backup <<'CRON'
# Sauvegarde PostgreSQL de Prière & Coran (salawat.dimatlas.com)
0 4 * * * root /opt/salawat/deploy/backup-db.sh >> /var/log/salawat-backup.log 2>&1
CRON
chmod 644 /etc/cron.d/salawat-backup
```

Résultat attendu au premier essai :

```
OK db-20261125-040000-123.sql.gz (36K) — 1 sauvegarde(s) conservée(s)
```

Le script refuse de créer une sauvegarde vide ou corrompue (`gzip -t` + taille minimale),
évite les exécutions simultanées (`flock`) et n'écrit le fichier final qu'une fois la
sauvegarde complète.

## 2. Vérifier que ça fonctionne

```bash
tail -n 5 /var/log/salawat-backup.log       # dernières exécutions
ls -lht /var/backups/salawat | head         # la plus récente date d'aujourd'hui ?
```

Une taille qui chute brutalement d'un jour à l'autre est un signal d'alerte.

## 3. Copie hors de la VPS (fortement recommandé)

Une sauvegarde qui reste sur le même serveur ne protège pas d'une panne du disque
ou de la VPS. Deux moyens simples :

- **Depuis votre ordinateur** (à lancer régulièrement ou par cron local) :

  ```bash
  rsync -az root@187.124.184.110:/var/backups/salawat/ ~/sauvegardes/salawat/
  ```

- **Instantanés Hostinger** : activez les sauvegardes automatiques / snapshots de la VPS
  dans hPanel (ils couvrent tout le disque, y compris le portail `dimatlas`).

Conservez les copies sur un support **chiffré** : elles contiennent des e-mails et
des mots de passe hachés (base) et des secrets (`env-*.bak`).

## 4. Restaurer

```bash
sudo /opt/salawat/deploy/restore-db.sh /var/backups/salawat/db-AAAAMMJJ-HHMMSS-mmm.sql.gz
```

Le script :

1. contrôle l'archive ;
2. demande de taper `RESTAURER` (**remplace toutes les données actuelles**) ;
3. crée d'abord une sauvegarde de sécurité de l'état actuel ;
4. arrête `backend`, `worker`, `worker-default`, `beat` ;
5. recrée le schéma et importe la sauvegarde ;
6. redémarre la stack.

Vérifiez ensuite :

```bash
curl -s https://salawat.dimatlas.com/health/        # {"status": "ok"}
```

### Restauration sur une nouvelle VPS

1. Redéployer l'application (voir `HANDOFF.md`) avec le `.env` sauvegardé
   (`env-AAAAMMJJ.bak` → `/opt/salawat/.env`, `chmod 600`) : mêmes clés VAPID.
2. Démarrer la stack, puis lancer `restore-db.sh` avec la sauvegarde.

### Tester la restauration (à faire une fois)

Une sauvegarde jamais restaurée n'est pas une garantie. Sur votre machine de développement :

```bash
APP_DIR=$PWD COMPOSE_FILES="-f docker-compose.yml" BACKUP_DIR=/tmp/essai deploy/backup-db.sh
APP_DIR=$PWD COMPOSE_FILES="-f docker-compose.yml" BACKUP_DIR=/tmp/essai \
  deploy/restore-db.sh /tmp/essai/db-….sql.gz
```

Ce scénario a été exécuté sur la base de développement : sauvegarde, ajout d'une table
témoin, restauration, vérification (table témoin supprimée, 108 comptes intacts).
Il n'a **pas** encore été exécuté sur la VPS de production.

## 5. Variables des scripts

| Variable | Défaut | Rôle |
|---|---|---|
| `APP_DIR` | `/opt/salawat` | dossier du projet |
| `COMPOSE_FILES` | `-f docker-compose.prod.yml -f docker-compose.vps.yml` | fichiers Compose |
| `BACKUP_DIR` | `/var/backups/salawat` | destination |
| `KEEP_DAYS` | `30` | rétention en jours |
| `ASSUME_YES` | — | `1` = restauration sans confirmation (déconseillé) |

## 6. Limites

- Le portail `dimatlas` (autre projet Docker de la VPS) n'est **pas** couvert par ces scripts.
- Pas de chiffrement des sauvegardes sur la VPS (protégées par les droits `root` uniquement).
- La restauration interrompt l'application quelques secondes à quelques minutes.
