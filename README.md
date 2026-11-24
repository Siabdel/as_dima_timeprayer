# Prière & Coran (Dima Time Prayer)

Hamdou li ALLAH. Application web (PWA) sans publicité : horaires de prière,
rappels Adhan, lecture et écoute du Saint Coran, calendrier hégirien,
outils (Qibla, tasbih) et bibliothèque.

## Stack

| Couche | Technologie |
|---|---|
| Backend | Django + Django REST Framework, Celery (worker + beat), PostgreSQL, Redis |
| Frontend | Vue 3, Pinia, Vue Router, Bootstrap 5, Vite, PWA (service worker Workbox) |
| Sources externes | Aladhan (horaires), Quran.com API v4 (texte, audio, mots, horodatages), Open-Meteo (météo) |
| Déploiement | Docker Compose, Caddy (HTTPS) — voir [DEPLOYMENT.md](DEPLOYMENT.md) |

## Fonctionnalités

- **Horaires de prière** par ville ou coordonnées, compte à rebours, méthodes de calcul par organisme.
- **Météo** de la ville sous les horaires (Open-Meteo via `GET /api/v1/weather/`, cache 15 min) : température °C/°F, précipitations, humidité, vent, courbe 24 h, prévisions 8 jours.
- **Coran** : 114 sourates, traductions FR/EN, audio par sourate ou verset, plusieurs récitateurs.
  - *Lecture mot à mot* : séquence de mots isolés avec traduction.
  - *Suivi de la récitation* : pendant l'écoute d'une sourate, le **verset** (ou le **mot**)
    récité est surligné et la page défile automatiquement (horodatages Quran.com).
  - *Récitateurs hébergés localement* : **Cheikh Abderrahmane Benmoussa** et
    **Cheikh Abdelhamid Hssain** (114 sourates chacun, MP3 servis par
    l'application — voir ci-dessous).
- **Réglages** (compte connecté) :
  - *Ma position* : lieu des horaires et de la météo (géolocalisation ou ville). Les visiteurs sans compte la gardent sur l'accueil.
  - *Fuseau, calcul et langue* : fuseau horaire auto/manuel (IANA), méthode de calcul par pays, langue.
  - *Alertes & Adhan* : mode par prière (sonnerie, bip, vibreur, silencieux), Adhan du Fajr,
    volume, fade-in, rappel avant l'Adhan.
  - *Audio* : récitateur par défaut avec aperçu, cache audio hors ligne vidable.
  - Notifications push, son de l'Adhan, profil.
- Calendrier hégirien et fêtes, outils (Qibla, tasbih), bibliothèque.

## Récitateurs hébergés localement

Certains récitateurs ne sont pas disponibles sur les CDN (quran.com, mp3quran.net).
Leurs MP3 sont alors **hébergés par l'application** (`frontend/public/quran/<slug>/`)
pour garantir la disponibilité et éviter toute dépendance externe.

| Récitateur | Riwaya | Sourates | Taille | Source |
|---|---|---|---|---|
| **Cheikh Abderrahmane Benmoussa** | Hafs | 114 (001.mp3 … 114.mp3) | 833 Mo (64 kbps) | archive.org `AbdulrahmanBenmoussa` |
| **Cheikh Abdelhamid Hssain** | Warsh | 114 (001.mp3 … 114.mp3) | 516 Mo | archive.org `abdelhamed-hssain-warsh` |

**Intégration** : catalogue [`local_reciters.py`](backend/apps/quran/local_reciters.py),
exposé par `GET /quran/reciters/` (avec `local: true`). `GET /quran/audio/chapter/{n}/?reciter_id=benmoussa`
renvoie `/quran/benmoussa/00N.mp3`. Le sélecteur de récitateur du lecteur audio accepte
les identifiants **numériques** (CDN externe) comme **textuels** (local).

**Ajouter un récitateur local** :
1. Déposer les MP3 dans `frontend/public/quran/<slug>/001.mp3 … 114.mp3`
2. Ajouter une entrée dans `LOCAL_RECITERS` (`local_reciters.py`).

> ⚠️ Ces fichiers (~833 Mo) ne sont pas versionnés dans Git ; assurez-vous de les
> inclure dans le déploiement (rsync, volume, ou objet storage).

## Démarrage

```bash
cp .env.example .env        # renseigner SECRET_KEY, mots de passe, etc.
docker compose up --build
```

- API : `/api/v1/` (contrat dans [openapi.yaml](openapi.yaml)), santé : `/health/`.
- Frontend de dev : `cd frontend && npm install && npm run dev`.

## Tests

```bash
# Backend (nécessite SECRET_KEY dans l'environnement)
cd backend && pip install -r requirements/dev.txt
SECRET_KEY=test python -m pytest -q

# Frontend : build, puis E2E Playwright (pile lancée)
cd frontend && npm run build && npm run test:e2e
```

## Structure

```
backend/apps/   accounts, prayer_times, notifications, quran, events, library, locations, tools
backend/config/ settings, urls, celery
frontend/src/   views, components, stores (Pinia), services, api, utils, sw.js
```

## Documents

[DEPLOYMENT.md](DEPLOYMENT.md) · [TODO.md](TODO.md) · [HANDOFF.md](HANDOFF.md) · [openapi.yaml](openapi.yaml)
