# Prière & Coran (Dima Time Prayer)

Hamdou li ALLAH. Application web (PWA) sans publicité : horaires de prière,
rappels Adhan, lecture et écoute du Saint Coran, calendrier hégirien,
outils (Qibla, tasbih) et bibliothèque.

## Stack

| Couche | Technologie |
|---|---|
| Backend | Django + Django REST Framework, Celery (worker + beat), PostgreSQL, Redis |
| Frontend | Vue 3, Pinia, Vue Router, Bootstrap 5, Vite, PWA (service worker Workbox) |
| Sources externes | Aladhan (horaires), Quran.com API v4 (texte, audio, mots, horodatages) |
| Déploiement | Docker Compose, Caddy (HTTPS) — voir [DEPLOYMENT.md](DEPLOYMENT.md) |

## Fonctionnalités

- **Horaires de prière** par ville ou coordonnées, compte à rebours, méthodes de calcul par organisme.
- **Coran** : 114 sourates, traductions FR/EN, audio par sourate ou verset, plusieurs récitateurs.
  - *Lecture mot à mot* : séquence de mots isolés avec traduction.
  - *Suivi de la récitation* : pendant l'écoute d'une sourate, le **verset** (ou le **mot**)
    récité est surligné et la page défile automatiquement (horodatages Quran.com).
- **Réglages** (compte connecté) :
  - *Ma position* : fuseau horaire auto/manuel (IANA), méthode de calcul par pays, langue.
  - *Alertes & Adhan* : mode par prière (sonnerie, bip, vibreur, silencieux), Adhan du Fajr,
    volume, fade-in, rappel avant l'Adhan.
  - *Audio* : récitateur par défaut avec aperçu, cache audio hors ligne vidable.
  - Notifications push, son de l'Adhan, profil.
- Calendrier hégirien et fêtes, outils (Qibla, tasbih), bibliothèque.

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
