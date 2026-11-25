# Procédure de déploiement — Prière & Coran

> Guide **générique**. Pour la procédure réellement suivie sur la VPS Hostinger
> (`salawat.dimatlas.com`, cohabitation avec le portail, nginx hôte), voir [DEPLOY.md](DEPLOY.md).

Ce document décrit **deux chemins de déploiement** pour l'application :

| Partie | Cible | Contenu |
|---|---|---|
| **A** | 🖥️ **VPS Hostinger** (Debian 13 « trixie ») | Docker Compose en production, HTTPS via Caddy, sauvegardes, mises à jour |
| **B** | 📱 **Google Play Store** | Transformation de la PWA en app Android (TWA) via Bubblewrap, publication |

> Les deux chemins ne sont pas exclusifs : la Partie B **nécessite** que l'application
> soit d'abord hébergée en HTTPS (donc déployée comme en Partie A ou sur un hébergeur
> équivalent). Le Play Store ne publie pas l'application elle-même — il publie un
> « lanceur » natif (TWA) qui ouvre votre site PWA dans Chrome sans barre d'adresse.

---

## Sommaire

- [Prérequis communs](#prérequis-communs)
- [Partie A — Déploiement sur un VPS Hostinger](#partie-a--déploiement-sur-un-vps-hostinger)
  - [A1. Commande du VPS et du domaine](#a1-commande-du-vps-et-du-domaine)
  - [A2. Préparation du serveur (sécurité)](#a2-préparation-du-serveur-sécurité)
  - [A3. Installation de Docker](#a3-installation-de-docker)
  - [A4. Récupération du code](#a4-récupération-du-code)
  - [A5. Configuration du fichier `.env` de production](#a5-configuration-du-fichier-env-de-production)
  - [A6. Premier lancement](#a6-premier-lancement)
  - [A7. Vérification post-déploiement](#a7-vérification-post-déploiement)
  - [A8. Sauvegardes](#a8-sauvegardes)
  - [A9. Mises à jour](#a9-mises-à-jour)
  - [A10. Monitoring et montée en charge (Ramadan)](#a10-monitoring-et-montée-en-charge-ramadan)
  - [A11. Dépannage](#a11-dépannage)
- [Partie B — Publication sur le Google Play Store](#partie-b--publication-sur-le-google-play-store)
  - [B1. Prérequis](#b1-prérequis)
  - [B2. Installer les outils (Bubblewrap, JDK)](#b2-installer-les-outils-bubblewrap-jdk)
  - [B3. Générer la clé de signature Android](#b3-générer-la-clé-de-signature-android)
  - [B4. Initialiser le projet TWA](#b4-initialiser-le-projet-twa)
  - [B5. Construire l'AAB](#b5-construire-laab)
  - [B6. Vérification d'actifs numériques (assetlinks.json)](#b6-vérification-dactifs-numériques-assetlinksjson)
  - [B7. Créer le compte Google Play Console](#b7-créer-le-compte-google-play-console)
  - [B8. Créer l'application et remplir la fiche](#b8-créer-lapplication-et-remplir-la-fiche)
  - [B9. Envoyer l'AAB en production](#b9-envoyer-laab-en-production)
  - [B10. Après la publication](#b10-après-la-publication)
  - [B11. Alternative : PWABuilder](#b11-alternative--pwabuilder)
- [Checklist finale](#checklist-finale)

---

## Prérequis communs

Quel que soit le chemin, préparez :

1. **Un domaine** (ex. `priere-coran.example.com`) — indispensable pour le HTTPS,
   le service worker et le Play Store. Chez Hostinger, achetez-le dans
   *Domaines → Acheter*, ou transférez un domaine existant.
2. **Un compte Quran Foundation** (API v4) : créez-le sur <https://quran.foundation>,
   demandez l'accès API, notez `QURAN_CLIENT_ID` et `QURAN_CLIENT_SECRET`.
3. **Une paire de clés VAPID** pour les notifications Web Push :
   ```bash
   npx web-push generate-vapid-keys
   ```
   Notez les deux clés (publique et privée). La clé publique est servie par
   l'API ; la privée ne quitte jamais le serveur.
4. **Les accès externes** vérifiés : l'API Aladhan est publique (aucune clé),
   l'API Quran.com nécessite les identifiants ci-dessus.

---

## Partie A — Déploiement sur un VPS Hostinger

### A1. Commande du VPS et du domaine

1. Sur <https://hpanel.hostinger.com> → **VPS → Créer un nouveau serveur**.
2. Choisissez :
   - **Template** : Debian 13 « trixie » (sans panneau de contrôle). Si vous
     choisissez « Clean OS », vous obtenez un système minimal : aucune
     infrastructure déjà installée, tout se fait en ligne de commande.
   - **Plan** : minimum **KVM 2** (2 vCPU / 8 Go RAM) pour la stack complète
     (PostgreSQL + Redis + 3 workers Celery + gunicorn + nginx + Caddy).
     Le KVM 1 (4 Go) peut suffire en début de vie, mais sera juste pendant Ramadan.
   - **Région** : la plus proche de votre audience (Europe pour la France).
3. Définissez un **mot de passe root** ou ajoutez votre **clé SSH** (recommandé).
4. **DNS** : dans *Domaines → votre-domaine → DNS / Nameservers* :
   - **Option recommandée** : gardez les DNS Hostinger et ajoutez un enregistrement
     **A** : `priere-coran` → `IP_PUBLIQUE_DU_VPS` (l'IP est affichée dans hPanel).
   - TTL 3600 s. La propagation prend de quelques minutes à quelques heures.
5. Vérifiez la propagation depuis votre machine :
   ```bash
   dig +short priere-coran.example.com
   # → doit renvoyer l'IP du VPS
   ```

> ⚠️ N'utilisez pas un sous-domaine partagé « *.hostinger.app » : le Play Store
> exige un domaine dont vous contrôlez la vérification d'actifs numériques.

### A2. Préparation du serveur (sécurité)

Connectez-vous : `ssh root@IP_DU_VPS`. Puis, **tout en root** :

```bash
# 1. Mise à jour complète
apt update && apt upgrade -y

# 2. sudo : Debian minimal ne l'installe PAS par défaut
apt install -y sudo

# 3. Créer un utilisateur d'administration (éviter root au quotidien)
adduser deploy
usermod -aG sudo deploy

# 4. SSH : clé publique pour l'utilisateur deploy
mkdir -p /home/deploy/.ssh
cp /root/.ssh/authorized_keys /home/deploy/.ssh/   # si vous avez une clé
chown -R deploy:deploy /home/deploy/.ssh
chmod 700 /home/deploy/.ssh && chmod 600 /home/deploy/.ssh/authorized_keys

# 5. Durcir SSH : désactiver root et les mots de passe
#    ⚠️ Debian 13 : vérifier qu'aucun drop-in cloud-init ne surcharge ces
#    réglages (sinon les lignes ci-dessous seraient ignorées) :
ls /etc/ssh/sshd_config.d/*.conf 2>/dev/null   # si des fichiers existent, les vérifier
sed -i 's/^#\?PermitRootLogin.*/PermitRootLogin no/' /etc/ssh/sshd_config
sed -i 's/^#\?PasswordAuthentication.*/PasswordAuthentication no/' /etc/ssh/sshd_config
systemctl restart ssh

# 6. Pare-feu : SSH, HTTP, HTTPS uniquement
apt install -y ufw
ufw default deny incoming
ufw default allow outgoing
ufw allow 22/tcp    # SSH
ufw allow 80/tcp    # HTTP (ACME Let's Encrypt)
ufw allow 443/tcp   # HTTPS
ufw allow 443/udp   # HTTP/3
ufw --force enable

# 7. Anti brute-force SSH
apt install -y fail2ban
systemctl enable --now fail2ban

# 8. Synchronisation horaire (critique pour les horaires de prière !)
timedatectl set-timezone Europe/Paris
timedatectl   # vérifier "System clock synchronized: yes"
```

Déconnectez-vous puis reconnectez-vous avec le nouvel utilisateur :
`ssh deploy@IP_DU_VPS`.

### A3. Installation de Docker

```bash
# Dépendances + clé GPG + dépôt officiel Docker (variante DEBIAN)
sudo apt install -y ca-certificates curl gnupg
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/debian/gpg | \
  sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg

# VERSION_CODENAME vaut "trixie" sur Debian 13 ; le dépôt officiel couvre trixie.
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
https://download.docker.com/linux/debian $(. /etc/os-release && echo $VERSION_CODENAME) stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Installation
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io \
  docker-buildx-plugin docker-compose-plugin

# Docker sans sudo pour l'utilisateur deploy
sudo usermod -aG docker deploy
newgrp docker   # ou se déconnecter/reconnecter

# Vérification
docker --version && docker compose version
```

### A4. Récupération du code

**Option 1 — Git (recommandé)** : poussez le projet sur GitHub/GitLab (en privé),
puis :

```bash
sudo mkdir -p /opt/priere-coran
sudo chown deploy:deploy /opt/priere-coran
git clone git@github.com:votre-compte/dimatimeprayer.git /opt/priere-coran
cd /opt/priere-coran
```

**Option 2 — Transfert direct** depuis votre poste de développement :

```bash
rsync -avz --exclude node_modules --exclude .git \
  ./dimatimeprayer/ deploy@IP_DU_VPS:/opt/priere-coran/
```

### A5. Configuration du fichier `.env` de production

```bash
cd /opt/priere-coran
cp .env.example .env
chmod 600 .env    # accessible uniquement au propriétaire
nano .env
```

Renseignez **chacune** des variables :

| Variable | Valeur en production | Comment générer |
|---|---|---|
| `SECRET_KEY` | Chaîne aléatoire de 50+ caractères | `python3 -c "import secrets; print(secrets.token_urlsafe(50))"` |
| `DEBUG` | **`False`** | — |
| `DJANGO_SETTINGS_MODULE` | **`config.settings.prod`** | — |
| `DJANGO_ALLOWED_HOSTS` | `priere-coran.example.com,localhost` | votre domaine |
| `FRONTEND_URL` | `https://priere-coran.example.com` | — |
| `CORS_ALLOWED_ORIGINS` | `https://priere-coran.example.com` | — |
| `CSRF_TRUSTED_ORIGINS` | `https://priere-coran.example.com` | requis pour l'admin derrière le proxy |
| `POSTGRES_DB` | `prayer_coran` | — |
| `POSTGRES_USER` | `prayer` | — |
| `POSTGRES_PASSWORD` | Mot de passe fort | `openssl rand -base64 32` |
| `DB_HOST` | `db` | nom du service compose |
| `DB_PORT` | `5432` | port interne Docker |
| `REDIS_URL` | `redis://redis:6379/0` | cache |
| `CELERY_BROKER_URL` | `redis://redis:6379/1` | broker |
| `CELERY_RESULT_BACKEND` | `redis://redis:6379/2` | résultats |
| `ALADHAN_API_BASE_URL` | `https://api.aladhan.com/v1` | — |
| `QURAN_API_BASE_URL` | `https://api.quran.com/api/v4` | — |
| `QURAN_CLIENT_ID` / `QURAN_CLIENT_SECRET` | Vos identifiants Quran Foundation | compte quran.foundation |
| `VAPID_PUBLIC_KEY` / `VAPID_PRIVATE_KEY` | Clés générées (prérequis 3) | `npx web-push generate-vapid-keys` |
| `VAPID_ADMIN_EMAIL` | `admin@example.com` | contact pour les erreurs push |
| `VITE_API_BASE_URL` | **`/api/v1`** | chemins relatifs : le navigateur appelle le même domaine (nginx proxifie `/api/`) |
| `VITE_VAPID_PUBLIC_KEY` | Copie de `VAPID_PUBLIC_KEY` | optionnel (l'API la sert aussi) |
| `TZ` | `Europe/Paris` | fuseau des conteneurs |

> ⚠️ **Important** : `VITE_API_BASE_URL=/api/v1` (relatif). En production, le
> frontend et l'API sont servis sur le **même domaine** via nginx → pas de CORS,
> pas de cookie cross-origin, et les préférences JWT fonctionnent sans autre
> configuration. Le build Vite est généré avec cette valeur au moment du
> `docker compose build`.

### A6. Premier lancement

```bash
cd /opt/priere-coran

# 1. Remplacer VOTRE_DOMAINE dans le Caddyfile par votre domaine réel
sed -i 's/VOTRE_DOMAINE/priere-coran.example.com/g' deploy/Caddyfile

# 2. Construire les images (backend gunicorn + frontend nginx)
docker compose -f docker-compose.prod.yml build

# 3. Démarrer la stack complète + le reverse proxy TLS
docker compose -f docker-compose.prod.yml -f docker-compose.caddy.yml up -d

# 4. Suivre les logs jusqu'à ce que tout soit vert
docker compose -f docker-compose.prod.yml -f docker-compose.caddy.yml logs -f
#   - backend : "migrate... OK", "gunicorn ... Listening at: http://0.0.0.0:8000"
#   - caddy   : "certificate obtained successfully" (première demande Let's Encrypt)
#   Ctrl+C pour quitter (les conteneurs continuent en arrière-plan)
```

À ce stade, Caddy a :

1. répondu au challenge ACME HTTP-01 sur le port 80 ;
2. obtenu le certificat Let's Encrypt pour votre domaine ;
3. activé la redirection automatique HTTP → HTTPS.

**Créer le superutilisateur Django** :

```bash
docker compose -f docker-compose.prod.yml exec backend \
  python manage.py createsuperuser
```

### A7. Vérification post-déploiement

Depuis votre poste :

```bash
# 1. Healthcheck
curl -s https://priere-coran.example.com/health/
# → {"status": "ok"}

# 2. Redirection HTTP → HTTPS
curl -sI http://priere-coran.example.com | head -1
# → HTTP/1.1 308 Permanent Redirect (gérée par Caddy)

# 3. API horaires de prière (cache Redis actif au 2e appel)
curl -s "https://priere-coran.example.com/api/v1/prayer-times/?latitude=48.8566&longitude=2.3522" | head -c 300

# 4. Frontend + PWA
curl -s -o /dev/null -w '%{http_code}\n' https://priere-coran.example.com/
curl -s https://priere-coran.example.com/manifest.webmanifest | head -c 200
```

Puis dans un navigateur :

1. Ouvrez `https://priere-coran.example.com` — cadenas visible, certificat valide.
2. **Testez le parcours complet** : inscription → connexion → horaires →
   lecture du Coran → Qibla → Tasbih → paramètres.
3. **Testez une notification push** : Paramètres → Notifications push →
   *Activer* → *Envoyer une notification de test* (nécéssite HTTPS + une
   permission accordée).
4. **Lighthouse** (Chrome DevTools → onglet Lighthouse, catégorie *PWA*) :
   installez l'application depuis la barre d'adresse — c'est ce test qui
   conditionne la Partie B.
5. **Admin Django** : `https://priere-coran.example.com/admin/` avec le
   superutilisateur créé.

### A8. Sauvegardes

**Sauvegarde quotidienne de la base** (cron) :

```bash
sudo mkdir -p /var/backups/priere-coran
sudo chown deploy:deploy /var/backups/priere-coran

crontab -e
```

Ajoutez :

```cron
# Sauvegarde PostgreSQL quotidienne à 04:00, conservation 30 jours
0 4 * * * cd /opt/priere-coran && docker compose -f docker-compose.prod.yml exec -T db \
  pg_dump -U prayer prayer_coran | gzip > /var/backups/priere-coran/db-$(date +\%Y\%m\%d).sql.gz
0 5 * * * find /var/backups/priere-coran -name 'db-*.sql.gz' -mtime +30 -delete
```

**Restauration** (à tester au moins une fois !) :

```bash
gunzip -c /var/backups/priere-coran/db-AAAAMMJJ.sql.gz | \
  docker compose -f docker-compose.prod.yml exec -T db \
  psql -U prayer -d prayer_coran
```

**Sauvegarde externe** : copiez les archives vers un stockage distant
(Hostinger propose des backups VPS automatiques — activez-les dans hPanel ;
sinon `rclone` vers un S3/Backblaze). Incluez aussi :
- le fichier `.env` (hors du dépôt git !) ;
- le volume `caddy_data` (certificats) ;
- le keystore Android de la Partie B (surtout !).

### A9. Mises à jour

```bash
cd /opt/priere-coran
git pull origin main

# Reconstruire et redémarrer sans coupure longue
docker compose -f docker-compose.prod.yml build
docker compose -f docker-compose.prod.yml -f docker-compose.caddy.yml up -d

# Les migrations sont appliquées automatiquement au démarrage du backend.
# Vérifier ensuite :
docker compose -f docker-compose.prod.yml ps
curl -s https://priere-coran.example.com/health/
```

En cas de problème après une mise à jour :

```bash
docker compose -f docker-compose.prod.yml logs backend --tail 100
# Revenir en arrière :
git checkout TAG_PRÉCÉDENT
docker compose -f docker-compose.prod.yml -f docker-compose.caddy.yml up -d --build
```

### A10. Monitoring et montée en charge (Ramadan)

**Surveillance minimale** :

```bash
# État des services
docker compose -f docker-compose.prod.yml ps

# Consommation
docker stats --no-stream

# Logs en continu
docker compose -f docker-compose.prod.yml logs -f backend worker worker-default beat
```

Ajoutez un monitoring externe gratuit (UptimeRobot, Better Uptime…) qui
interroge `https://priere-coran.example.com/health/` toutes les 5 minutes et
vous alerte par e-mail.

**Pic Ramadan** : le scheduler `beat` scanne les notifications toutes les
5 minutes et le worker `notifications` est isolé sur sa file dédiée. Pour
absorber un pic :

```bash
# Ajouter un 2e worker de notifications (scale)
docker compose -f docker-compose.prod.yml up -d --scale worker=3
```

**Vérification des tâches Celery** :

```bash
docker compose -f docker-compose.prod.yml exec backend \
  python -c "from config.celery import app; print(app.control.inspect().stats().keys())"
```

### A11. Dépannage

| Symptôme | Diagnostic | Solution |
|---|---|---|
| `502 Bad Gateway` | backend arrêté | `docker compose -f docker-compose.prod.yml logs backend` puis `up -d` |
| Certificat non obtenu | DNS pas propagé, port 80 bloqué | `dig +short priere-coran.example.com` ; `ufw status` ; attendre puis redémarrer Caddy |
| `400 Invalid HTTP_HOST` | domaine absent de `DJANGO_ALLOWED_HOSTS` | corriger `.env` puis `up -d` |
| `CSRF verification failed` (admin) | `CSRF_TRUSTED_ORIGINS` manquant | ajouter `https://votre-domaine` dans `.env` puis `up -d` |
| Notifications jamais envoyées | worker arrêté ou Redis plein | `docker compose -f docker-compose.prod.yml logs worker` ; `docker compose exec redis redis-cli -n 1 ping` |
| `ImproperlyConfigured` au démarrage | secret manquant (`SECRET_KEY`, `REDIS_URL`…) | relire la table A5, tout compléter |
| Admin sans CSS | volume `static_data` vide | `docker compose -f docker-compose.prod.yml exec backend python manage.py collectstatic --noinput` |
| Disque plein | logs Docker | `docker system prune -af` (attention : supprime les images inutilisées) |

---

## Partie B — Publication sur le Google Play Store

> **Principe** : l'application est une **PWA**. Le Play Store ne peut pas
> publier un site web directement : on construit une **TWA** (Trusted Web
> Activity), un conteneur Android minimal qui ouvre votre site dans Chrome
> **sans barre d'adresse ni interface navigateur**. Toute la logique reste
> sur votre serveur : une mise à jour du site = une mise à jour de l'app,
> sans repasser par le Play Store (sauf changement de permissions natives).

### B1. Prérequis

- [ ] **Application déployée en HTTPS** (Partie A terminée) sur un domaine
      que vous contrôlez : `https://priere-coran.example.com`.
- [ ] **Lighthouse PWA** ≥ 90 sur la page d'accueil (Chrome DevTools).
      Points vérifiés par le Play Store :
      - `manifest.webmanifest` servi avec icônes 192 px et 512 px ;
      - service worker enregistré (généré par vite-plugin-pwa) ;
      - HTTPS valide.
- [ ] **Compte Google Play Console** : <https://play.google.com/console>.
      Frais d'inscription unique **25 $** (paiement, puis vérification
      d'identité — comptez 1 à 3 jours).
- [ ] Un poste de développement avec **Node.js 18+** et **Java JDK 17+** (21 conseillé).

### B2. Installer les outils (Bubblewrap, JDK)

Sur votre machine de développement (pas le VPS) :

```bash
# JDK (Bubblewrap exige Java 17+). Sur Debian 13 « trixie », la version
# disponible dans les dépôts est OpenJDK 21 :
sudo apt install -y openjdk-21-jdk
# Windows : adoptium.net  |  macOS : brew install --cask temurin@21

# Vérifier
java -version    # → openjdk version "21.x" (ou 17+)

# Bubblewrap (CLI officielle de Google pour les TWA)
npm install -g @bubblewrap/cli
bubblewrap --version
```

### B3. Générer la clé de signature Android

```bash
bubblewrap keygen --keystore priere-coran.keystore
# Répondre : mot de passe du keystore, alias (ex : pc-release),
# mot de passe de l'alias, nom/organisation…
```

> ⚠️ **Sauvegardez ce keystore** (`priere-coran.keystore` + mots de passe +
> alias) dans un gestionnaire de mots de passe ET sur un support physique.
> Sans lui, impossible de publier une mise à jour de l'application.
> (En dernier recours, le *Play App Signing* de Google permet une remise à
> zéro de la clé — mais il faut le configurer avant la première publication.)

### B4. Initialiser le projet TWA

```bash
mkdir priere-coran-twa && cd priere-coran-twa

# Bubblewrap télécharge votre manifest et pré-remplit tout
bubblewrap init --manifest https://priere-coran.example.com/manifest.webmanifest
```

Bubblewrap pose des questions ; répondez :

| Question | Réponse |
|---|---|
| Package name (identifiant unique) | `fr.votredomaine.prierecoran` (jamais à changer ensuite) |
| Nom de l'app | `Prière & Coran` |
| URL de départ | `https://priere-coran.example.com/` |
| Mode d'affichage | `standalone` |
| Thème de la barre de statut | `#14746F` (vert de l'app) |
| Splash screen | icône 512 px + couleur de fond `#14746F` |
| Keystore | `priere-coran.keystore` (créé en B3) |

Cela génère `twa-manifest.json` — personnalisez-le si besoin
(`twa edit` pour le modifier plus tard).

### B5. Construire l'AAB

```bash
bubblewrap build --skipPwaValidation
# → app-release-bundle.aab  (bundle à uploader sur le Play Store)
```

> `--skipPwaValidation` évite l'échec si le serveur de validation de
> Bubblewrap est indisponible ; les vraies vérifications sont faites en B6.

### B6. Vérification d'actifs numériques (assetlinks.json)

Pour que la TWA s'ouvre **sans barre d'adresse**, votre site doit déclarer
qu'il « fait confiance » à l'application Android. Il faut servir :

```
https://priere-coran.example.com/.well-known/assetlinks.json
```

**1. Récupérer l'empreinte SHA-256 de votre certificat** :

```bash
keytool -list -v -keystore priere-coran.keystore -alias pc-release \
  | grep "SHA256:"
```

**2. Générer le JSON** (Bubblewrap le fait pour vous) :

```bash
bubblewrap statement create  # ou lire le fichier généré automatiquement
```

Il ressemble à :

```json
[{
  "relation": ["delegate_permission/common.handle_all_urls"],
  "target": {
    "namespace": "android_app",
    "package_name": "fr.votredomaine.prierecoran",
    "sha256_cert_fingerprints": ["AB:CD:EF:…:01"]
  }
}]
```

**3. Le placer dans le projet** : créez
`frontend/public/.well-known/assetlinks.json` avec ce contenu (Vite copie
`public/` vers `dist/` au build), puis **reconstruisez et redéployez le
frontend** :

```bash
# sur le VPS
cd /opt/priere-coran
git pull origin main
docker compose -f docker-compose.prod.yml build frontend
docker compose -f docker-compose.prod.yml up -d frontend
```

**4. Vérifier** :

```bash
curl -s https://priere-coran.example.com/.well-known/assetlinks.json
# → le JSON ci-dessus

# et l'outil officiel de Google :
# https://developers.google.com/digitalassetlinks/v1/statements/list
#   ?source.web.site=https://priere-coran.example.com&relation=delegate_permission/common.handle_all_urls
```

> ⚠️ Google cache les vérifications : après avoir déployé le fichier,
> attendez quelques minutes avant de tester sur un appareil.

### B7. Créer le compte Google Play Console

1. <https://play.google.com/console> → **Commencer** → payer les 25 $.
2. Compléter le **profil développeur** : nom, adresse, e-mail de contact.
3. Vérification d'identité (document d'identité) — 1 à 3 jours.
4. **Compte de développeur** : une fois validé, vous pouvez créer des apps.

### B8. Créer l'application et remplir la fiche

1. **Créer une app** : nom « Prière & Coran », langue par défaut **Français**,
   type **Application**, gratuit/payant : **Gratuit**.
2. **Fiche Play Store** (*Store listing*) :
   - **Titre** (30 car. max) : `Prière & Coran`
   - **Description courte** (80 car.) : `Horaires de prière, rappels Adhan, Coran audio, Qibla et calendrier hégirien`
   - **Description complète** : détailler les 7 fonctionnalités MVP, mentionner
     « aucune publicité, respectueuse de la vie privée ».
   - **Icône d'app** : 512 × 512 px PNG (réutiliser `public/icons/icon-512.png`).
   - **Bannière** : 1024 × 500 px (à créer).
   - **Captures d'écran** : minimum 2, 16:9 ou 9:16, jusqu'à 8 — prenez des
     captures réelles : horaires du jour, lecture du Coran (RTL arabe),
     boussole Qibla, Tasbih, notifications.
   - **Lien politique de confidentialité** (obligatoire) : hébergez une page
     simple (ex. `https://priere-coran.example.com/privacy/` — route statique
     à ajouter dans le frontend, ou un fichier sur le VPS).
3. **Classification du contenu** : questionnaire IARC — app religieuse,
   aucune violence/publicité, tous publics.
4. **Public cible** : 18+ (ou 13+ selon votre choix), *pas* une app pour enfants.
5. **Sécurité des données** (*Data safety*) — déclarez honnêtement :
   - **Collectées** : adresse e-mail (compte), identifiants d'appareil
     (abonnement push), position géographique **approximative ou précise** si
     la géolocalisation est utilisée pour Qibla — précisez qu'elle n'est
     **jamais stockée côté serveur** sauf si l'utilisateur enregistre un lieu
     par défaut (dans ce cas : « données utilisateur, sauvegardées,
     supprimables sur demande »).
   - **Partagées** : aucune avec des tiers.
   - **Chiffrées en transit** : oui (HTTPS).
   - **Suppression sur demande** : oui (prévoir un e-mail de contact).
6. **Accès à l'application** (*App access*) : déclarer que l'inscription est
   libre (fournir des identifiants de test si une partie nécessite un compte).

### B9. Envoyer l'AAB en production

1. **Production → Créer une version**.
2. Uploader `app-release-bundle.aab`.
3. **Notes de version** : `Première version : horaires de prière, rappels
   Adhan, Coran audio, Qibla, calendrier hégirien, Tasbih.`
4. **Programmes de test** (recommandé) : envoyez d'abord en
   *Test interne* (jusqu'à 100 testeurs) ou *Test fermé* (20+ testeurs,
   14 jours conseillés pour un premier lancement) — cela améliore la qualité
   perçue et évite les rejets.
5. **Envoyer pour examen**. Délai habituel : **quelques heures à 7 jours**.
6. Statuts possibles : *Approuvée* → publication ; *Refusée* → lisez
   l'e-mail de Google (les motifs fréquents : politique de confidentialité
   manquante, captures trompeuses, données non déclarées) — corrigez et
   renvoyez.

### B10. Après la publication

- **Mises à jour du site** : transparentes pour l'app (la TWA affiche le site
  en direct). Aucune action Play Store nécessaire.
- **Mise à jour de l'app** (ex. changement de nom, icône, permissions) :
  modifier `twa-manifest.json` → `bubblewrap build` → uploader la nouvelle
  version **avec le même keystore** → *Envoyer pour examen*.
- **Notifications push** : elles fonctionnent dans la TWA (le moteur est
  Chrome). Testez sur un appareil réel : permission → abonnement → test.
- **Statistiques** : Play Console → *Statistiques* (installations, désinstallations,
  crashs).
- **Répondre aux avis** : la section *Notes et avis* — une réponse sous 24 h
  améliore la visibilité.

### B11. Alternative : PWABuilder

Si vous ne voulez pas utiliser la ligne de commande :

1. Ouvrez <https://www.pwabuilder.com> et entrez l'URL de votre PWA.
2. Vérifiez le score (manifest, service worker, sécurité).
3. **Package for stores → Android** → options de signature (fournissez votre
   keystore ou laissez PWABuilder le générer) → téléchargez le `.aab`.
4. Le JSON `assetlinks.json` est fourni dans le zip — placez-le comme en B6.

> PWABuilder et Bubblewrap produisent le même type de TWA ; choisissez
> l'outil avec lequel vous êtes le plus à l'aise. Bubblewrap reste plus fin
> pour les mises à jour ultérieures.

> **iPhone / App Store** : Apple ne propose pas de TWA. Les options sont
> PWABuilder pour iOS (également disponible) ou un wrapper Capacitor —
> hors périmètre de ce document, mais le même socle PWA est réutilisable.

---

## Checklist finale

### Avant mise en production (Partie A)

- [ ] Domaine + DNS configurés, propagation vérifiée
- [ ] Serveur à jour, SSH durci, pare-feu actif (22/80/443 uniquement)
- [ ] Docker + Compose installés
- [ ] `.env` complet (tous les secrets réels), `chmod 600`, jamais commité
- [ ] `deploy/Caddyfile` : domaine remplacé
- [ ] Stack démarrée : 6 services `Up` + caddy
- [ ] Certificat Let's Encrypt actif (cadenas)
- [ ] `/health/` → `{"status": "ok"}`
- [ ] Parcours complet testé : inscription → horaires → Coran → Qibla → push
- [ ] Superutilisateur créé, admin accessible
- [ ] Sauvegarde PostgreSQL cron configurée, restauration testée
- [ ] Monitoring externe sur `/health/`

### Avant publication Play Store (Partie B)

- [ ] Lighthouse PWA ≥ 90
- [ ] Keystore Android sauvegardé en lieu sûr (2 copies)
- [ ] `assetlinks.json` servi et vérifié sur le domaine
- [ ] Compte Play Console créé et vérifié
- [ ] Fiche complète : description, icônes, captures, politique de confidentialité
- [ ] Questionnaire *Data safety* rempli honnêtement
- [ ] Test interne validé sur un appareil réel (installation, notifications)
- [ ] AAB signé avec le bon keystore, envoyé, examen en cours

---

*Document généré pour le projet « Prière & Coran » — MVP conteneurisé
(Django 5 + DRF + Celery / PostgreSQL 16 + Redis 7 / Vue 3 + Vite PWA),
docker-compose.prod.yml + docker-compose.caddy.yml + deploy/Caddyfile.*
