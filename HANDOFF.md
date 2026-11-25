# HANDOFF — état du projet

Dernière mise à jour : 2026-11-24. Branche `main`.

## Dernier travail (2 commits)
1. `728615c` **Suivi de la récitation** (verset par verset / mot par mot).
2. `b39a99b` **Réglages avancés** (position, alertes/Adhan, récitateur, cache audio).

## Suivi de la récitation — comment ça marche
- Backend : `quran_client.fetch_chapter_audio` appelle Quran.com `/chapter_recitations/{id}/{n}?segments=true` et
  `normalize_timestamps` renvoie `timestamps: [{ayah, from, to, segments:[[pos_mot, début_ms, fin_ms]]}]`
  via `GET /api/v1/quran/audio/chapter/{n}/`.
- Store `frontend/src/stores/quranPlayer.js` : `followMode` (`off|ayah|word`, persisté `pc_follow_mode`),
  `chapterTimestamps`, `followAyah`, `followWordIndex`. Une boucle `requestAnimationFrame` (démarrée sur `play`,
  stoppée sur `pause`/`ended`) appelle `_syncFollow()`. `seekToWord()` saute à un mot.
- UI : `SurahView.vue` (sélecteur radio « Suivi de la récitation »), `VerseList.vue` (surbrillance
  `pc-verse-following`, `scrollIntoView` centré, respecte `prefers-reduced-motion`).
- Distinct de l'interrupteur « Lecture mot à mot » (mp3 de mots isolés, `wordsQueue`), qui est inchangé.

## Réglages avancés — comment ça marche
- Modèle `UserPreference` (migration `accounts/0004`) : `timezone_mode`, `timezone`, `language`, `alert_modes` (JSON),
  `reminder_minutes_before` (0/5/10/15/30), `fajr_adhan_sound_id`, `adhan_volume`, `adhan_fade_in`.
  Validation dans `accounts/serializers.py` ; contrat dans `openapi.yaml`.
- Notifications (`notifications/tasks.py`) : mode `silent` ignoré ; `_sound_url_for` (Adhan du Fajr, pas de son hors mode `full`) ;
  `send_prayer_reminder` déclenché par `scan_prayer_notifications` ; payload push enrichi (`alert_mode`, `volume`, `fade_in`).
- Client : `sw.js` (vibreur, transmission des options, **cache audio** `pc-audio-v1` CacheFirst + Range, max 40),
  `services/adhanAudio.js` (volume, fade-in, `playBeep`), `components/SettingsPreferencesPanel.vue` (sections A/B/C),
  `utils/calcMethods.js` (méthodes Aladhan, pays → méthode, fuseaux).
- Correction : Maroc = méthode **21**, Russie = **14** (étaient inversés dans `PrayerTimesView`).

## Lancer / tester
- Docker dev : le service `backend` lance `migrate` au démarrage.
- Backend : pas de venv dans le dépôt. Exemple : `python3 -m venv /tmp/venv && /tmp/venv/bin/pip install -r backend/requirements/dev.txt`,
  puis `cd backend && SECRET_KEY=test /tmp/venv/bin/python -m pytest -q` (134 tests verts au dernier passage).
- Frontend : `cd frontend && npx vite build` (OK). Les E2E Playwright n'ont **pas** été lancés.

## Pièges
- `settings.base` exige `SECRET_KEY` dans l'environnement.
- Le dossier `frontend/dist` n'est pas suivi par git.
- Un hook « GateGuard » local demande de justifier les premières commandes/éditions d'un fichier.
- L'ancien tableau `METHODS` de `PrayerTimesView` est remplacé par `CALC_METHODS` ; ne pas le réintroduire.

## Prochaines étapes
Voir [TODO.md](TODO.md) (vérifications navigateur, migration prod, limites connues).

## PWA (v0.2.0)
- `sw.js` appelle maintenant `skipWaiting()` + `clientsClaim()` : sans cela, avec `registerType: 'autoUpdate'`, une nouvelle version restait « en attente » tant qu'un onglet était ouvert.
- Manifeste : `id`, `scope`, catégories et raccourcis (Horaires, Coran, Réglages).
- Le service worker n'est actif qu'en build de production (`npm run build` / image `prod` + nginx), pas avec `npm run dev`.
- Les récitations locales (`public/quran/`, 816 Mo) ne sont pas pré-cachées ni cachées par le SW.

## Déploiement VPS Hostinger (salawat.dimatlas.com)
- **Où :** VPS KVM 2 (Debian 13, `187.124.184.110`), projet Compose `dimatimeprayer-prod` dans `/opt/salawat`.
  Cohabite avec le portail existant (`/home/django/dimatlas-portal`, projet `dimatlas`, 127.0.0.1:8000) — ne pas y toucher.
- **Réseau :** frontend (nginx conteneur) publié sur `127.0.0.1:8081` (`docker-compose.vps.yml`). Le nginx de l'hôte
  (`/etc/nginx/sites-available/salawat.dimatlas.com`, modèle : `deploy/nginx-salawat.conf`) porte le HTTPS (certbot, renouvellement auto).
- **DNS :** enregistrement A `salawat` → IP de la VPS (zone `dimatlas.com`).
- **Secrets :** `/opt/salawat/.env` (chmod 600, hors dépôt) : SECRET_KEY, mots de passe, clés VAPID générées au déploiement. `LOCAL_RECITERS_ENABLED=true` + `LOCAL_RECITERS_SURAHS=100-114` : seul l'audio des 15 petites sourates de Benmoussa est déployé (`/opt/salawat/frontend/public/quran/benmoussa/`, 3,9 Mo). Les autres sourates renvoient un 404 explicite. Pour en ajouter : copier les mp3, élargir `LOCAL_RECITERS_SURAHS`, `up -d --build`.
- **Mise à jour :**
  ```bash
  rsync -az --delete --exclude .git --exclude node_modules --exclude frontend/dist --exclude frontend/public/quran \
    --exclude frontend/.playwright-browsers --exclude .env -e "ssh -i ~/.ssh/salawat_deploy" ./ root@187.124.184.110:/opt/salawat/
  ssh -i ~/.ssh/salawat_deploy root@187.124.184.110 'cd /opt/salawat && docker compose -f docker-compose.prod.yml -f docker-compose.vps.yml up -d --build'
  ```
- **Accès :** la clé SSH dédiée au déploiement (`claude-deploy-salawat`) a été **retirée** de la VPS et supprimée en local (2026-11-25). Pour une mise à jour : ajouter une nouvelle clé (hPanel ou API Hostinger), exécuter les commandes ci-dessus, puis la retirer.
- **À faire :** `docker compose ... exec backend python manage.py createsuperuser` pour l'admin Django.
