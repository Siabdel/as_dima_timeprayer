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
