# DEPLOY — Procédure de déploiement sur la VPS Hostinger (salawat.dimatlas.com)

Procédure **réellement suivie** le 2026-11-25 pour mettre « Prière & Coran » en ligne
sur la VPS Hostinger, à côté du portail `dimatlas` déjà en production. Pour la
procédure générique (VPS vierge, Caddy, Play Store), voir [DEPLOYMENT.md](DEPLOYMENT.md).

| Document | Contenu |
|---|---|
| **DEPLOY.md** (ce fichier) | Déploiement sur *cette* VPS, mises à jour, pièges rencontrés |
| [BACKUP.md](BACKUP.md) | Sauvegarde / restauration (app + portail) |
| [PARTAGER.md](PARTAGER.md) | Partager l'app, installer la PWA |
| [HANDOFF.md](HANDOFF.md) | État du projet, notes de passation |

## Sommaire

1. [Architecture](#1-architecture)
2. [Prérequis et identifiants](#2-prérequis-et-identifiants)
3. [Déploiement initial pas à pas](#3-déploiement-initial-pas-à-pas)
4. [Audio de Benmoussa (partiel)](#4-audio-de-benmoussa-partiel)
5. [Contrôles après déploiement](#5-contrôles-après-déploiement)
6. [Mettre à jour l'application](#6-mettre-à-jour-lapplication)
7. [Compte administrateur Django](#7-compte-administrateur-django)
8. [Partager l'app (QR code)](#8-partager-lapp-qr-code)
9. [Sauvegardes](#9-sauvegardes)
10. [Gestion de l'accès SSH](#10-gestion-de-laccès-ssh)
11. [Pièges rencontrés et solutions](#11-pièges-rencontrés-et-solutions)
12. [Retour arrière](#12-retour-arrière)
13. [Check-list](#13-check-list)

---

## 1. Architecture

```
Internet ──HTTPS──▶ nginx (hôte, ports 80/443, certbot)
                      ├─ dimatlas.com / www            → site existant (ne pas toucher)
                      ├─ portail.dimatlas.com          → 127.0.0.1:8000 (projet Docker « dimatlas »)
                      └─ salawat.dimatlas.com ─────────→ 127.0.0.1:8081 (projet « dimatimeprayer-prod »)
                                                            │
                                    frontend (nginx conteneur, SPA + PWA)
                                      ├─ /api/, /admin/ ─▶ backend (gunicorn)
                                      └─ backend ─ PostgreSQL ─ Redis ─ Celery worker/beat
```

| Élément | Valeur |
|---|---|
| VPS | Hostinger KVM 2, Debian 13, id `1599443`, IP `187.124.184.110` |
| Domaine de l'app | `salawat.dimatlas.com` (enregistrement DNS A, zone `dimatlas.com`) |
| Dossier sur la VPS | `/opt/salawat` |
| Projet Compose | `dimatimeprayer-prod` (isolé : réseau, volumes, conteneurs propres) |
| Fichiers Compose | `docker-compose.prod.yml` + `docker-compose.vps.yml` |
| Port local publié | `127.0.0.1:8081` → frontend (jamais exposé à Internet) |
| HTTPS | nginx de l'hôte + `certbot --nginx` (renouvellement automatique) |
| Secrets | `/opt/salawat/.env` (`chmod 600`, hors dépôt) |

> **Règle d'or :** le portail `dimatlas` (`/home/django/dimatlas-portal`) est en production.
> Ne jamais y toucher, ne pas utiliser Caddy (les ports 80/443 appartiennent au nginx de l'hôte).

## 2. Prérequis et identifiants

- Connecteur **Hostinger** autorisé dans Claude Code (OAuth) : lecture des VPS, DNS, gestion des clés SSH.
- Accès SSH `root` à la VPS par **clé dédiée et temporaire** (voir [§10](#10-gestion-de-laccès-ssh)).
- Docker 29 + Compose v5 déjà installés sur la VPS ; `rsync` disponible.
- Pas de `.env` dans le dépôt : il est généré pour le déploiement (§3.3).

## 3. Déploiement initial pas à pas

### 3.1 DNS (ajout uniquement, sans toucher aux autres enregistrements)

Via l'API Hostinger (`dns_records_update`, `overwrite: false`) ou hPanel :

| Nom | Type | Valeur | TTL |
|---|---|---|---|
| `salawat` | A | `187.124.184.110` | 300 |

Vérifier la propagation avant le certificat :

```bash
dig +short salawat.dimatlas.com @1.1.1.1      # → 187.124.184.110
```

### 3.2 Envoyer le code (sans l'audio lourd)

```bash
KEY=~/.ssh/salawat_deploy
SSHO="ssh -i $KEY -o IdentitiesOnly=yes -o BatchMode=yes"

$SSHO root@187.124.184.110 'mkdir -p /opt/salawat'
rsync -az --delete -e "$SSHO" \
  --exclude .git --exclude node_modules --exclude frontend/dist --exclude frontend/dev-dist \
  --exclude frontend/public/quran --exclude frontend/.playwright-browsers \
  --exclude '__pycache__' --exclude '.pytest_cache' --exclude .env \
  --exclude backend/db.sqlite3 --exclude frontend/test-results --exclude frontend/playwright-report \
  ./ root@187.124.184.110:/opt/salawat/
```

Taille attendue : **~16 Mo**. Si c'est plus, une exclusion manque (voir [§11](#11-pièges-rencontrés-et-solutions)).

### 3.3 Générer le `.env` de production

Les secrets (SECRET_KEY, mot de passe PostgreSQL, clés VAPID) sont générés **en local**,
puis copiés en `chmod 600` ; ils ne sont jamais écrits dans le dépôt ni affichés.

```python
# mkenv.py — python3 mkenv.py prod.env   (nécessite : pip install cryptography)
import base64, secrets, sys
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import serialization
b64 = lambda b: base64.urlsafe_b64encode(b).rstrip(b"=").decode()
k = ec.generate_private_key(ec.SECP256R1())
priv = b64(k.private_numbers().private_value.to_bytes(32, "big"))
pub = b64(k.public_key().public_bytes(serialization.Encoding.X962,
                                      serialization.PublicFormat.UncompressedPoint))
host = "salawat.dimatlas.com"
admin_email = "<votre-adresse-e-mail>"   # contact transmis aux services de push (VAPID)
open(sys.argv[1], "w").write(f"""SECRET_KEY={secrets.token_urlsafe(60)}
DEBUG=False
DJANGO_SETTINGS_MODULE=config.settings.prod
DJANGO_ALLOWED_HOSTS={host},localhost,backend,127.0.0.1
FRONTEND_URL=https://{host}
CORS_ALLOWED_ORIGINS=https://{host}
CSRF_TRUSTED_ORIGINS=https://{host}
POSTGRES_DB=prayer_coran
POSTGRES_USER=prayer
POSTGRES_PASSWORD={secrets.token_urlsafe(32)}
DB_HOST=db
DB_PORT=5432
REDIS_URL=redis://redis:6379/0
CELERY_BROKER_URL=redis://redis:6379/1
CELERY_RESULT_BACKEND=redis://redis:6379/2
ALADHAN_API_BASE_URL=https://api.aladhan.com/v1
QURAN_API_BASE_URL=https://api.quran.com/api/v4
QURAN_CLIENT_ID=
QURAN_CLIENT_SECRET=
VAPID_PUBLIC_KEY={pub}
VAPID_PRIVATE_KEY={priv}
VAPID_ADMIN_EMAIL={admin_email}
VITE_API_BASE_URL=/api/v1
VITE_VAPID_PUBLIC_KEY={pub}
LOCAL_RECITERS_ENABLED=true
LOCAL_RECITERS_IDS=benmoussa
LOCAL_RECITERS_SURAHS=100-114
THROTTLE_ANON=1500/hour
THROTTLE_USER=5000/hour
TZ=Europe/Paris
""")
```

```bash
chmod 600 prod.env
scp -i $KEY -o IdentitiesOnly=yes prod.env root@187.124.184.110:/opt/salawat/.env
ssh -i $KEY root@187.124.184.110 'chmod 600 /opt/salawat/.env'
shred -u prod.env                              # supprimer la copie locale
```

> `QURAN_CLIENT_ID/SECRET` vides = accès anonyme à l'API Quran.com.

### 3.4 Construire et lancer la stack

```bash
ssh -i $KEY root@187.124.184.110
cd /opt/salawat
docker compose -f docker-compose.prod.yml -f docker-compose.vps.yml up -d --build
docker compose -f docker-compose.prod.yml -f docker-compose.vps.yml ps
curl -s -H "Host: salawat.dimatlas.com" -H "X-Forwarded-Proto: https" http://127.0.0.1:8081/health/
# → {"status": "ok"}
```

Le backend applique les migrations et `collectstatic` au démarrage.

### 3.5 nginx de l'hôte + certificat

```bash
cp /opt/salawat/deploy/nginx-salawat.conf /etc/nginx/sites-available/salawat.dimatlas.com
ln -sf ../sites-available/salawat.dimatlas.com /etc/nginx/sites-enabled/salawat.dimatlas.com
nginx -t && systemctl reload nginx             # toujours tester avant de recharger
certbot --nginx -d salawat.dimatlas.com --non-interactive --agree-tos --redirect
nginx -t
```

Certbot réutilise le compte Let's Encrypt existant et ajoute le bloc HTTPS + la
redirection. Les autres sites (`dimatlas.com`, `portail`) ne sont pas modifiés.

## 4. Audio de Benmoussa (partiel)

Les 114 mp3 pèsent ~816 Mo ; seules les **sourates 100 à 114** (15 fichiers, 3,9 Mo) sont déployées.

```bash
$SSHO root@187.124.184.110 'mkdir -p /opt/salawat/frontend/public/quran/benmoussa'
rsync -az -e "$SSHO" frontend/public/quran/benmoussa/1{0,1}?.mp3 \
  root@187.124.184.110:/opt/salawat/frontend/public/quran/benmoussa/
```

Dans `/opt/salawat/.env` :

```ini
LOCAL_RECITERS_ENABLED=true
LOCAL_RECITERS_IDS=benmoussa      # seuls les récitateurs locaux dont les MP3 sont déployés
LOCAL_RECITERS_SURAHS=100-114
```

> `LOCAL_RECITERS_IDS` évite d'afficher un récitateur dont l'audio n'est pas sur le serveur
> (ex. `hssain` : ses fichiers ne sont pas déployés). `LOCAL_RECITERS_SURAHS` s'applique à
> tous les récitateurs listés.

Puis `up -d --build` (les mp3 sont intégrés à l'image du frontend). L'API refuse proprement
les autres sourates (404 « Cette sourate n'est pas disponible pour ce récitateur »).

- **Ajouter d'autres sourates :** copier les mp3, élargir `LOCAL_RECITERS_SURAHS` (ex. `1-114`), reconstruire.
- **Masquer complètement Benmoussa :** `LOCAL_RECITERS_ENABLED=false`.
- Droits de diffusion de cet enregistrement non clarifiés (voir [PARTAGER.md](PARTAGER.md) §10).

## 5. Contrôles après déploiement

```bash
U=https://salawat.dimatlas.com
curl -s $U/health/                                         # {"status": "ok"}
curl -sI http://salawat.dimatlas.com | head -1             # 301 vers HTTPS
curl -s $U/manifest.webmanifest | head -c 120              # manifeste PWA
curl -s -o /dev/null -w "%{http_code}\n" $U/sw.js          # 200
curl -s "$U/api/v1/prayer-times/?city=Casablanca&country=Maroc&method=21" | head -c 150
curl -s "$U/api/v1/weather/?city=Casablanca" | head -c 150
curl -s "$U/api/v1/events/france/?year=2026" | head -c 100
curl -s "$U/api/v1/quran/audio/chapter/112/?reciter_id=benmoussa"     # /quran/benmoussa/112.mp3
curl -s -w " [%{http_code}]\n" "$U/api/v1/quran/audio/chapter/2/?reciter_id=benmoussa"   # 404 attendu
curl -sI $U/quran/benmoussa/112.mp3 | grep -i -E "^HTTP|content-type|accept-ranges"
for h in dimatlas.com portail.dimatlas.com; do curl -s -o /dev/null -w "$h %{http_code}\n" https://$h/; done   # inchangés
```

Puis sur un téléphone : ouvrir le site, créer un compte, choisir un lieu, installer la PWA,
activer les notifications (Réglages) et envoyer la notification de test.

## 6. Mettre à jour l'application

1. Ajouter une clé SSH temporaire ([§10](#10-gestion-de-laccès-ssh)).
2. Envoyer le code (commande du §3.2) — le `.env` et l'audio ne sont pas écrasés (exclus).
3. Reconstruire et relancer :

   ```bash
   ssh -i $KEY root@187.124.184.110 \
     'cd /opt/salawat && docker compose -f docker-compose.prod.yml -f docker-compose.vps.yml up -d --build'
   ```

4. Refaire les contrôles du §5. Les migrations s'appliquent au redémarrage du backend.
5. **Retirer la clé SSH.**

Les utilisateurs de la PWA reçoivent la nouvelle version à leur prochaine ouverture
(service worker avec `skipWaiting`).

## 7. Compte administrateur Django

Sur la VPS (le projet utilise l'**e-mail** comme identifiant) :

```bash
cd /opt/salawat && docker compose -f docker-compose.prod.yml -f docker-compose.vps.yml \
  exec backend python manage.py createsuperuser
```

Connexion : <https://salawat.dimatlas.com/admin/>. Choisir un mot de passe fort ; répondre `N`
si Django propose de contourner la validation.

## 8. Partager l'app (QR code)

- Dans l'app : **Réglages → Partager l'application** (QR code, bouton Partager du téléphone,
  copie du lien, téléchargement du QR). Le QR encode l'adresse du site ouvert.
- QR autonome : `qrcode` (npm) —
  `node -e "require('qrcode').toFile('qr.png','https://salawat.dimatlas.com/',{width:800,margin:3})"`.
- Installation côté amis : [PARTAGER.md](PARTAGER.md) §7.

## 9. Sauvegardes

Scripts prêts, **à installer sur la VPS** : voir [BACKUP.md](BACKUP.md).

| Cible | Script | Cron conseillé |
|---|---|---|
| Prière & Coran | `deploy/backup-db.sh` → `/var/backups/salawat` | 04:00 |
| Portail dimatlas (base + médias) | `deploy/backup-portail.sh` → `/var/backups/dimatlas` | 04:30 |

Copier aussi les sauvegardes **hors** de la VPS (rsync vers votre poste) et activer les
instantanés Hostinger.

## 10. Gestion de l'accès SSH

L'accès SSH est donné **temporairement**, par clé dédiée, via l'API Hostinger :

```bash
ssh-keygen -t ed25519 -N "" -C "claude-deploy-salawat" -f ~/.ssh/salawat_deploy
```

| Étape | Opération Hostinger |
|---|---|
| Lister les clés | `vps_ssh-keys_list-virtual-machine` (`virtualMachineId: 1599443`) |
| Ajouter | `vps_ssh-keys_add-virtual-machine` (`keys: ["<clé publique>"]`) — clé ajoutée à `root` |
| Retirer | `vps_ssh-keys_remove-virtual-machine` (même clé) |

Après usage : retirer la clé côté Hostinger, puis en local
`shred -u ~/.ssh/salawat_deploy; rm ~/.ssh/salawat_deploy.pub; ssh-keygen -R 187.124.184.110`.
Vérifier que l'accès est coupé (`Permission denied (publickey,password)`).
Le 2026-11-25, la clé a été retirée à la fin du déploiement.

> Les autres clés de la VPS (`claude-deploy-dimatlas-vps` et celles du propriétaire du compte)
> appartiennent à d'autres accès : ne pas les retirer.

## 11. Pièges rencontrés et solutions

| Problème | Cause | Solution appliquée |
|---|---|---|
| Frontend appelant `localhost:8000` en prod | `VITE_API_BASE_URL` absent du contexte de build (le `.env` n'est pas dans `frontend/`) | `src/api/client.js` : `/api/v1` par défaut en production |
| Boucle de redirections HTTPS (Django) | Le nginx du conteneur envoyait `X-Forwarded-Proto: http` | `frontend/nginx/default.conf` : `map` qui conserve l'en-tête du proxy amont |
| `collectstatic` : `Permission denied: /app/staticfiles` | Volume nommé créé en `root` | `backend/Dockerfile` : `mkdir` + `chown app` de `/app/staticfiles` ; supprimer le volume `…_static_data` s'il existe déjà |
| Dossier envoyé de 716 Mo | `frontend/.playwright-browsers` (700 Mo) inclus | Exclusion `rsync` + ajout à `frontend/.dockerignore` |
| `rsync --delete` ne supprime pas les exclus | Les fichiers exclus sont protégés côté destination | Les supprimer à la main sur la VPS |
| Requête HTTP brute → `301 https://backend:8000` | Normal : Django voit `X-Forwarded-Proto: http` avant la redirection nginx | Disparaît une fois le HTTPS certbot actif |
| Erreurs « Impossible de changer de récitateur » / aperçus muets | Limite de requêtes API de 100/h par visiteur, atteinte en quelques minutes ; aperçu sur la sourate 1 alors que Benmoussa n'a que 100-114 | `THROTTLE_ANON=1500/hour` (env), aperçu sur la sourate 112, messages d'erreur explicites (429, 404) et retour au récitateur précédent |
| Récitateur local visible sans audio | Catalogue exposé sans les MP3 déployés | `LOCAL_RECITERS_IDS` limite la liste aux récitateurs déployés |
| `curl …/quran/benmoussa/001.mp3` → 200 alors que le fichier n'existe pas | Repli SPA de nginx (`index.html`) | Sans conséquence : l'API répond 404 pour les sourates absentes |

## 12. Retour arrière

Le portail n'est jamais arrêté. Pour retirer l'application :

```bash
cd /opt/salawat && docker compose -f docker-compose.prod.yml -f docker-compose.vps.yml down        # garde les données
# destruction des données : ajouter -v (irréversible, après sauvegarde !)
rm /etc/nginx/sites-enabled/salawat.dimatlas.com && nginx -t && systemctl reload nginx
certbot delete --cert-name salawat.dimatlas.com
```

Puis supprimer l'enregistrement DNS `salawat` (hPanel ou `dns_records_delete`).

## 13. Check-list

- [x] DNS `salawat` ajouté, propagé
- [x] Code envoyé (16 Mo), `.env` de production généré (VAPID, mots de passe)
- [x] Stack Docker lancée (`dimatimeprayer-prod`), `/health/` OK
- [x] nginx de l'hôte + certificat Let's Encrypt, HTTP → HTTPS
- [x] Benmoussa : sourates 100-114 déployées
- [x] Clé SSH de déploiement retirée
- [ ] Compte administrateur Django créé ([§7](#7-compte-administrateur-django))
- [ ] Sauvegardes installées et copie hors VPS ([§9](#9-sauvegardes))
- [ ] Notifications d'Adhan testées de bout en bout sur téléphone
- [ ] Identifiants Quran Foundation renseignés (optionnel)
