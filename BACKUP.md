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
| `MEDIA_VOLUME` | — | volume Docker de fichiers à archiver aussi (portail) |
| `STOP_SERVICES` | `backend worker worker-default beat` | services arrêtés pendant la restauration |

## 6. Portail `dimatlas` (portail.dimatlas.com)

Le portail est un **autre projet Docker** de la même VPS (`/home/django/dimatlas-portal`,
projet Compose `dimatlas`). Il a sa base PostgreSQL **et** un volume de fichiers
téléversés (`mediafiles`). Deux scripts dédiés réutilisent les mêmes outils :

```bash
scp deploy/backup-portail.sh deploy/restore-portail.sh root@187.124.184.110:/opt/salawat/deploy/
```

Sur la VPS :

```bash
chmod 700 /opt/salawat/deploy/*-portail.sh
docker volume ls | grep mediafiles          # confirmer le nom : dimatlas_mediafiles
mkdir -p /var/backups/dimatlas && chmod 700 /var/backups/dimatlas

/opt/salawat/deploy/backup-portail.sh       # essai manuel
# si le volume se nomme autrement : MEDIA_VOLUME=<nom> /opt/salawat/deploy/backup-portail.sh

cat > /etc/cron.d/dimatlas-backup <<'CRON'
30 4 * * * root /opt/salawat/deploy/backup-portail.sh >> /var/log/dimatlas-backup.log 2>&1
CRON
chmod 644 /etc/cron.d/dimatlas-backup
```

Fichiers produits dans `/var/backups/dimatlas/` : `db-*.sql.gz` (base), `media-*.tar.gz`
(fichiers téléversés) et `env-*.bak` (`.env` du portail). Le script ne modifie rien dans
le portail : il lit la base (`pg_dump`) et le volume en lecture seule.

> **Non testé sur le portail.** Les scripts ont été écrits à partir de son fichier Compose
> (services `db`, `django`, `celery`, `celery_beat`, volume `mediafiles`) et testés en local
> sur la base de cette application, y compris l'archive d'un volume Docker. Faites un essai
> manuel et contrôlez le contenu avant de compter dessus.

## 7. Restaurer le portail

Base (remplace les données actuelles ; sauvegarde de sécurité automatique avant) :

```bash
sudo /opt/salawat/deploy/restore-portail.sh /var/backups/dimatlas/db-AAAAMMJJ-HHMMSS-mmm.sql.gz
```

Fichiers téléversés (manuel) : arrêter `django celery celery_beat`, vider le volume
`dimatlas_mediafiles`, y extraire l'archive `media-….tar.gz` avec un conteneur `alpine`
(`tar xzf … -C /data`), puis relancer le projet. Faites-le avec prudence : cette étape
**efface** le contenu actuel du volume.

## 8. Limites

- Le portail est couvert par `backup-portail.sh` (§6), mais cette procédure n'a pas été testée sur lui.
- Pas de chiffrement des sauvegardes sur la VPS (protégées par les droits `root` uniquement).
- La restauration interrompt l'application quelques secondes à quelques minutes.
