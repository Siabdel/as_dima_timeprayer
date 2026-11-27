# Fonctionnalité « Coran » — architecture technique

Lecture des sourates (texte, traductions, mot à mot) et récitation audio.

## 1. Vue d'ensemble

```
Navigateur (PWA Vue 3 + Pinia)
   │  1. appelle l'API Django : texte, liste des récitateurs, URL audio
   ▼
Backend Django REST (apps/quran)  ──►  Quran.com API v4 (texte, traductions, mots, URL audio)
   │  cache 24 h (cache Django / Redis)
   │  2. renvoie une URL audio (pas le fichier)
   ▼
Navigateur : <audio src="URL"> lit le MP3 directement depuis la source
```

Le backend ne transporte jamais les MP3. Il sert de proxy et de cache pour les
métadonnées, puis il renvoie au front l'URL du MP3.

## 2. Backend (`backend/apps/quran/`)

### Endpoints

Tous publics (sans authentification) sauf la progression de lecture.

| Endpoint | Rôle |
|---|---|
| `GET /api/v1/quran/surahs/` | liste des 114 sourates |
| `GET /api/v1/quran/surahs/{n}/?translations=fr,en&words=true` | versets en arabe Uthmani, traductions (5 max), mot à mot en option |
| `GET /api/v1/quran/reciters/` | récitateurs, séparés chapitre / verset |
| `GET /api/v1/quran/audio/chapter/{surah}/?reciter_id=` | URL du MP3 de la sourate + horodatages par verset et par mot |
| `GET /api/v1/quran/audio/verse/?surah&ayah&reciter_id` | URL de l'audio d'un seul verset |
| `GET /api/v1/quran/words/{surah}/{ayah}/` | mots d'un verset |
| `GET/PUT /api/v1/quran/progress/` | dernier verset lu (JWT requis) |

### API externe : Quran Foundation / Quran.com v4

Code : `services/quran_client.py`.

- Les appels sont faits côté serveur. L'authentification OAuth2
  `client_credentials` est optionnelle (`QURAN_CLIENT_ID` / `QURAN_CLIENT_SECRET`) :
  sans identifiants, l'appel est anonyme. Les secrets ne sont jamais exposés au front.
- Traductions = IDs de ressources Quran.com : `31` français (Hamidullah),
  `20` anglais (Saheeh International), `2` arabe simplifié.
- Les réponses sont normalisées en un format interne stable. Les notes de bas de
  page `<sup foot_note=...>` sont retirées du texte.
- Cache de 24 h (`_cached()` dans `views.py`), car le texte est statique. Cela
  protège l'API externe pendant les pics du Ramadan.
- Si Quran.com est indisponible : erreur 503 au format
  `{"error": {"code": "external_api_error", "message": "..."}}`.

### Base de données

- `ReadingProgress` : utilisateur, dernière sourate, dernier verset.
- Texte local (branche `dev_texte_QURAN_local`) : `Surah`, `Verse` (arabe Uthmani) et
  `VerseTranslation` (codes `fr` et `en`, avec l'ID de ressource Quran.com). Remplis par
  `python manage.py import_quran_text` (idempotent, ≈ 3 Mo).

Les vues lisent d'abord la base (`services/local_text.py`) et gardent exactement le format
de réponse de Quran.com. Elles retombent sur Quran.com (avec le cache 24 h) si la base est
vide, si la sourate est incomplète, si une traduction demandée manque ou si la langue n'est
pas importée (ex. `ar`). `QURAN_LOCAL_TEXT_ENABLED=false` force ce repli. L'audio, les
horodatages et le mot à mot restent externes.

## 3. Les MP3 : trois sources selon le récitateur

`fetch_chapter_audio()` choisit la source d'après `reciter_id` :

1. **Récitateurs locaux** (id texte : `benmoussa`, `hssain`)
   Les MP3 sont dans `frontend/public/quran/<slug>/001.mp3 … 114.mp3` et servis
   par nginx. L'URL est relative (`/quran/benmoussa/002.mp3`).
   Variables d'environnement (`local_reciters.py`) :
   - `LOCAL_RECITERS_ENABLED=false` : désactive tous les récitateurs locaux ;
   - `LOCAL_RECITERS_IDS="benmoussa,hssain"` : ne publie que ceux listés ;
   - `LOCAL_RECITERS_SURAHS="1,2,100-114"` : ne publie que certaines sourates
     (évite de déployer les ~816 Mo sur le VPS).
   Une sourate non déployée renvoie une erreur 404 `not_available`.
2. **Récitateurs « extra »** (marocains : Kazabri, Kouchi, Benkirane, Lharraz,
   Belalia) : streamés depuis `cdn.mp3quran.net/audio/<nom>/r1/<003d>.mp3`.
3. **Récitateurs Quran.com** (id numérique, défaut `7` = Mishary Alafasy) :
   `chapter_recitations/{id}/{surah}?segments=true` renvoie l'URL du MP3 et les
   `timestamps`.

## 4. Streaming audio

Oui, c'est de la lecture HTTP progressive. Le front fait `audioEl.src = url` sur
une balise `<audio>` HTML5 (`stores/quranPlayer.js`). Le navigateur envoie des
**requêtes HTTP Range** et lit le MP3 au fur et à mesure, ce qui permet de se
déplacer dans la sourate sans tout télécharger. Ce n'est ni du HLS ni du DASH :
c'est la lecture progressive d'un MP3 statique.

### Service Worker (`frontend/src/sw.js`)

- MP3 **externes** : stratégie `CacheFirst` dans le cache `pc-audio-v1`, avec
  `RangeRequestsPlugin` pour que le seek fonctionne depuis le cache. Ils sont
  écoutables hors ligne après une première lecture. Le cache peut être vidé
  depuis la page Réglages.
- MP3 **locaux** : non mis en cache par le SW, car ils sont déjà sur le même serveur.
- MP3 d'Adhan : non pré-cachés (5 Mo chacun).

## 5. Frontend (`frontend/src/`)

| Fichier | Rôle |
|---|---|
| `views/QuranView.vue` | liste des sourates |
| `views/SurahView.vue` | lecture d'une sourate |
| `components/SurahList.vue`, `VerseList.vue` | listes de sourates et de versets |
| `components/WordByWordReader.vue` | lecture mot à mot |
| `components/AudioPlayer.vue` | barre de lecture |
| `api/quran.js` | wrapper axios des endpoints |
| `stores/quranPlayer.js` | store Pinia du lecteur |

### Store `quranPlayer`

- Un **seul élément `<audio>`**, rendu dans `App.vue` et jamais démonté : la
  lecture continue quand on change de page.
- État : sourate, verset, URL, temps, durée, récitateur.
- Le récitateur choisi est persisté dans le `localStorage` (`pc_reciter_id`),
  comme le mode mot à mot (`pc_word_mode`) et le mode de suivi (`pc_follow_mode`).

### Suivi de la récitation

Trois modes : `off`, `ayah` (verset) et `word` (mot). Une boucle
`requestAnimationFrame` compare `audio.currentTime` aux horodatages en
millisecondes renvoyés par l'API, puis surligne le verset ou le mot en cours.
Sans horodatages (récitateurs locaux et « extra »), le suivi se dégrade sans erreur.

### Mode mot à mot

Un second objet `Audio` dédié enchaîne de petits MP3, un par mot, sans toucher
à la barre de lecture principale. Un mot en erreur est sauté.

## 6. Déploiement

Docker Compose, avec nginx devant (reverse proxy vers le backend, fichiers
statiques et MP3 locaux) et Caddy pour le TLS. Voir `DEPLOY.md`.

## 7. Points d'attention

- La disponibilité dépend de Quran.com et de `cdn.mp3quran.net`. Seuls les
  récitateurs locaux sont indépendants des services externes.
- Le cache de 24 h ne couvre pas `fetch_chapter_audio` : chaque lancement d'un
  récitateur Quran.com refait un appel externe. Le front gère le cas 429 avec un
  message dédié. Passer cet appel par `_cached` réduirait la charge.
