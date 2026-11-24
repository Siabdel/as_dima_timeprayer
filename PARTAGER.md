# Partager l'application « Prière & Coran » avec vos amis

Guide technique : mettre l'application en ligne sur votre **VPS Hostinger**, puis
donner un lien à vos amis pour qu'ils l'**installent comme une application**
(PWA) sur leur téléphone.

> Ce guide résume le chemin « partage ». Les détails serveur (sécurisation du
> VPS, sauvegardes, monitoring) sont dans [DEPLOYMENT.md](DEPLOYMENT.md), partie A.

## Sommaire

1. [Comment ça marche](#1-comment-ça-marche)
2. [Prérequis](#2-prérequis)
3. [Mise en ligne sur la VPS](#3-mise-en-ligne-sur-la-vps)
4. [Cas particulier : l'audio de Benmoussa (816 Mo)](#4-cas-particulier--laudio-de-benmoussa-816-mo)
5. [Vérifier avant de partager](#5-vérifier-avant-de-partager)
6. [Partager le lien](#6-partager-le-lien)
7. [Installation sur le téléphone des amis](#7-installation-sur-le-téléphone-des-amis)
8. [Notifications d'Adhan](#8-notifications-dadhan)
9. [Publier une mise à jour](#9-publier-une-mise-à-jour)
10. [Limites et points d'attention](#10-limites-et-points-dattention)
11. [Dépannage](#11-dépannage)
12. [Alternatives](#12-alternatives)

---

## 1. Comment ça marche

Une PWA n'est pas un fichier à envoyer : c'est un **site web** que le navigateur
peut installer. Partager l'app = partager une **adresse HTTPS**.

```
Téléphone d'un ami ──HTTPS──▶ Caddy (VPS, certificat Let's Encrypt)
                                   │
                                   ▼
                              nginx (frontend)
                       ┌───────────┼─────────────┐
                       ▼           ▼             ▼
                 site + PWA     /api/ ──▶ backend Django (gunicorn)
              (HTML/JS, sw.js)            ├─ PostgreSQL
                                          ├─ Redis
                                          └─ Celery worker + beat (notifications)
```

Points clés :

- **HTTPS obligatoire.** Sans HTTPS, le navigateur refuse le service worker,
  l'installation, les notifications push et la géolocalisation (sauf sur
  `localhost`). Caddy obtient le certificat automatiquement.
- **Même domaine pour le site et l'API.** nginx proxifie `/api/` vers Django :
  pas de CORS à configurer. Le frontend appelle `/api/v1` (chemin relatif).
- **Rien à envoyer aux amis** : ni fichier, ni store. Un lien suffit.

## 2. Prérequis

| Élément | Détail |
|---|---|
| VPS Hostinger | Debian 13, Docker + Docker Compose installés ([DEPLOYMENT.md A1–A3](DEPLOYMENT.md)) |
| Nom de domaine | Un domaine ou sous-domaine pointant vers l'IP de la VPS (enregistrement DNS **A**), ex. `priere.mondomaine.com` |
| Ports ouverts | 80 et 443 (TCP) et 443 (UDP, HTTP/3) sur le pare-feu |
| Clés VAPID | Pour les notifications : `npx web-push generate-vapid-keys` |
| Compte Quran Foundation | Identifiants API (`QURAN_CLIENT_ID` / `QURAN_CLIENT_SECRET`) |

Vérifiez le DNS avant de continuer :

```bash
dig +short priere.mondomaine.com      # doit afficher l'IP de la VPS
```

## 3. Mise en ligne sur la VPS

### 3.1 Envoyer le code

Depuis votre poste (dans le dossier du projet) :

```bash
rsync -avz --exclude node_modules --exclude .git --exclude frontend/dist \
  ./ deploy@IP_VPS:/opt/priere-coran/
```

> `rsync` envoie aussi `frontend/public/quran/` (audio de Benmoussa, 816 Mo) même
> s'il est ignoré par git — voir [§4](#4-cas-particulier--laudio-de-benmoussa-816-mo).

### 3.2 Configurer `.env`

```bash
ssh deploy@IP_VPS
cd /opt/priere-coran
cp .env.example .env && chmod 600 .env
nano .env
```

Valeurs essentielles (liste complète : [DEPLOYMENT.md A5](DEPLOYMENT.md)) :

```ini
SECRET_KEY=<python3 -c "import secrets; print(secrets.token_urlsafe(50))">
DEBUG=False
DJANGO_SETTINGS_MODULE=config.settings.prod
DJANGO_ALLOWED_HOSTS=priere.mondomaine.com,localhost
FRONTEND_URL=https://priere.mondomaine.com
CORS_ALLOWED_ORIGINS=https://priere.mondomaine.com
CSRF_TRUSTED_ORIGINS=https://priere.mondomaine.com
POSTGRES_PASSWORD=<openssl rand -base64 32>
VAPID_PUBLIC_KEY=...
VAPID_PRIVATE_KEY=...
VAPID_ADMIN_EMAIL=vous@mondomaine.com
TZ=Europe/Paris
```

> Le frontend de production appelle `/api/v1` par défaut (même origine) : vous
> n'avez **pas** besoin de régler `VITE_API_BASE_URL` pour le partage.

### 3.3 Domaine dans Caddy, puis lancement

```bash
sed -i 's/VOTRE_DOMAINE/priere.mondomaine.com/g' deploy/Caddyfile

docker compose -f docker-compose.prod.yml build
docker compose -f docker-compose.prod.yml -f docker-compose.caddy.yml up -d
docker compose -f docker-compose.prod.yml -f docker-compose.caddy.yml logs -f
```

Attendez dans les logs :

- backend : `migrate ... OK` puis `Listening at: http://0.0.0.0:8000` ;
- caddy : `certificate obtained successfully`.

Le backend applique les migrations au démarrage (commande de
`docker-compose.prod.yml`). Créez ensuite un administrateur :

```bash
docker compose -f docker-compose.prod.yml exec backend python manage.py createsuperuser
```

## 4. Cas particulier : l'audio de Benmoussa (816 Mo)

Les 114 mp3 de Cheikh Benmoussa sont dans `frontend/public/quran/benmoussa/`.
Ils sont **ignorés par git** (trop volumineux) mais **inclus dans le build**
Docker du frontend (Vite copie `public/` dans l'image nginx).

- Ils sont envoyés avec le `rsync` ci-dessus : prévoyez ~1 Go de disque libre en
  plus de l'image (≈ 2 Go le temps du build) et un envoi plus long la 1re fois.
- Un `git clone` sur la VPS ne contiendrait **pas** ces fichiers : si vous
  déployez par git, envoyez-les à part :

  ```bash
  rsync -avz --progress frontend/public/quran/ deploy@IP_VPS:/opt/priere-coran/frontend/public/quran/
  ```

- Sans ces fichiers, l'app fonctionne ; seul le récitateur Benmoussa renverra
  une erreur de lecture.
- Vérifiez que vous avez le **droit de diffuser** cet enregistrement à vos amis
  (voir [§10](#10-limites-et-points-dattention)).

## 5. Vérifier avant de partager

```bash
curl -s https://priere.mondomaine.com/health/                     # {"status": "ok"}
curl -sI http://priere.mondomaine.com | head -1                   # redirection vers HTTPS
curl -s "https://priere.mondomaine.com/api/v1/prayer-times/?city=Paris&country=France" | head -c 200
curl -s "https://priere.mondomaine.com/api/v1/weather/?city=Paris" | head -c 200
curl -sI https://priere.mondomaine.com/manifest.webmanifest | head -1   # 200
curl -sI https://priere.mondomaine.com/quran/benmoussa/001.mp3 | head -1 # 200
```

Puis, **dans un navigateur sur votre téléphone** :

1. Ouvrez l'adresse : cadenas valide, page d'accueil qui charge.
2. Créez un compte, connectez-vous, ouvrez Réglages.
3. Lisez une sourate (suivi verset par verset) et la météo sous les horaires.
4. Activez les notifications et envoyez la notification de test (Réglages →
   Notifications push).
5. Chrome DevTools → **Lighthouse** → catégorie PWA : l'app doit être
   « installable ».

## 6. Partager le lien

Envoyez simplement l'adresse (WhatsApp, SMS, e-mail) :

> Assalamou alaykoum ! Voici l'application : https://priere.mondomaine.com
> Ouvre le lien sur ton téléphone puis « Installer l'application » /
> « Sur l'écran d'accueil ». Tu peux créer un compte pour recevoir les rappels
> d'Adhan.

Option : générez un **QR code** de l'adresse (par exemple avec
`qrencode -o qr.png https://priere.mondomaine.com`) pour l'afficher ou
l'imprimer.

## 7. Installation sur le téléphone des amis

### Android (Chrome, Edge, Samsung Internet)

1. Ouvrir le lien dans **Chrome**.
2. Menu ⋮ → **Installer l'application** (ou bandeau « Ajouter à l'écran
   d'accueil »).
3. L'icône apparaît dans le tiroir d'applications. Appui long sur l'icône :
   raccourcis **Horaires de prière**, **Coran**, **Réglages**.

### iPhone / iPad (Safari uniquement)

1. Ouvrir le lien dans **Safari** (pas Chrome).
2. Bouton **Partager** → **Sur l'écran d'accueil** → **Ajouter**.
3. **Les notifications push ne fonctionnent que si l'app est installée ainsi**
   et sous **iOS/iPadOS 16.4 ou plus**. Il faut ensuite ouvrir l'app installée
   (pas Safari) et activer les notifications depuis Réglages.

### Ordinateur (Chrome / Edge)

Icône « Installer » dans la barre d'adresse.

## 8. Notifications d'Adhan

- Chaque ami doit **créer son compte** (e-mail + mot de passe), choisir son lieu,
  puis activer les notifications dans **Réglages → Notifications push**.
- Les rappels sont envoyés par le serveur (services `worker` et `beat`) : ils
  arrivent même app fermée. Vérifiez qu'ils tournent :

  ```bash
  docker compose -f docker-compose.prod.yml ps
  docker compose -f docker-compose.prod.yml logs --tail 50 beat worker
  ```

- Le **son de l'Adhan** ne se joue que si l'application est ouverte
  (limitation des navigateurs) ; app fermée, l'ami reçoit la notification, avec
  vibration selon le mode choisi.
- Sur Android, demandez de **désactiver l'optimisation de batterie** pour
  l'application si les notifications arrivent en retard.

## 9. Publier une mise à jour

```bash
# Poste local
rsync -avz --exclude node_modules --exclude .git --exclude frontend/dist \
  ./ deploy@IP_VPS:/opt/priere-coran/

# VPS
cd /opt/priere-coran
docker compose -f docker-compose.prod.yml build
docker compose -f docker-compose.prod.yml -f docker-compose.caddy.yml up -d
```

- Les migrations s'appliquent automatiquement au redémarrage du backend.
- **Les amis n'ont rien à faire** : le service worker active la nouvelle version
  dès l'ouverture de l'app (`skipWaiting`) et la page se recharge. (Une
  installation encore sur l'ancien service worker peut demander de fermer
  complètement l'app une fois.)
- Changement du frontend uniquement : `build frontend` puis `up -d` suffit.

## 10. Limites et points d'attention

- **Droits d'auteur.** L'audio de Benmoussa vient d'un site tiers (archive.org)
  dont les droits ne sont pas clairs. Pour un cercle d'amis, vérifiez que vous
  pouvez le diffuser ; pour un partage plus large, demandez l'autorisation ou
  retirez-le. Les récitateurs Quran.com / mp3quran.net sont streamés depuis
  leurs serveurs, pas hébergés par vous.
- **Données personnelles.** Les comptes stockent e-mail, préférences et position
  par défaut sur *votre* serveur. Informez vos amis, ne partagez pas la base, et
  mettez en place les sauvegardes ([DEPLOYMENT.md A8](DEPLOYMENT.md)).
- **Quotas des API externes.** Aladhan et Open-Meteo sont gratuits et publics ;
  l'application met les réponses en cache (météo 15 min, horaires via Redis).
  Quran.com demande vos identifiants API.
- **Pas de store.** Sur iOS, il n'y a pas d'équivalent à l'APK : l'installation
  passe obligatoirement par Safari. Pour Android uniquement, une publication
  Play Store est possible ([DEPLOYMENT.md partie B](DEPLOYMENT.md)).
- **Capacité.** Un VPS modeste suffit pour quelques dizaines d'amis ; surveillez
  l'espace disque (images Docker + 816 Mo d'audio).

## 11. Dépannage

| Symptôme | Cause probable | Solution |
|---|---|---|
| Page blanche / « Not Secure » | Certificat non émis, DNS pas encore propagé, ports 80/443 fermés | `dig` du domaine, pare-feu, logs `caddy` |
| `DisallowedHost` / erreur 400 | Domaine absent de `DJANGO_ALLOWED_HOSTS` | Corriger `.env`, `up -d` |
| Connexion impossible, erreur CSRF (admin) | `CSRF_TRUSTED_ORIGINS` manquant | Ajouter `https://votre-domaine` |
| L'app appelle `localhost:8000` | Ancienne image construite avant la correction | `build --no-cache frontend` puis `up -d` |
| Pas d'option « Installer » | Pas en HTTPS, manifest introuvable, Safari sur iOS | Vérifier `/manifest.webmanifest` ; iOS : « Sur l'écran d'accueil » |
| Notifications absentes sur iPhone | App non installée / iOS < 16.4 | Installer depuis Safari, iOS 16.4+ |
| Notification de test en erreur | Clés VAPID absentes/incohérentes | Regénérer, corriger `.env`, redémarrer backend |
| Rappels jamais envoyés | `worker`/`beat` arrêtés, ou aucun lieu enregistré | `docker compose ps`, définir un lieu dans Réglages |
| Récitateur Benmoussa muet | Fichiers audio absents de l'image | Voir [§4](#4-cas-particulier--laudio-de-benmoussa-816-mo), rebuild |
| Ancienne version après mise à jour | Service worker encore en cache | Fermer complètement l'app puis la rouvrir |
| Météo absente | Open-Meteo injoignable depuis la VPS | `curl https://api.open-meteo.com` depuis la VPS |

## 12. Alternatives

| Option | Quand l'utiliser | Limites |
|---|---|---|
| **Tunnel temporaire** (Cloudflare Tunnel, ngrok) | Démo de quelques heures depuis votre PC | URL qui change, PC allumé, push peu fiable |
| **Réseau local (Wi-Fi)** | Test à la maison | Pas de HTTPS → pas d'installation PWA, ni push, ni géolocalisation |
| **Play Store (TWA)** | Distribuer sur Android à grande échelle | Compte développeur payant, revue Google ([DEPLOYMENT.md B](DEPLOYMENT.md)) |

---

*Dernière mise à jour : 2026-11-24. Procédure rédigée à partir de la configuration
du dépôt (Caddy, nginx, docker-compose.prod.yml) ; elle n'a pas été exécutée de
bout en bout sur la VPS.*
