# Notes d'exploitation — Prière & Coran (Salawat)

Remarques de suivi, mises à jour le 2026-11-25 (dernière mise en ligne : bibliothèque chargée, menu responsive, Ramadan, rappels, 8 Adhan).

## Sauvegardes (VPS salawat.dimatlas.com)

- **Installé le 2026-11-25** : `deploy/backup-db.sh` et `restore-db.sh` dans `/opt/salawat/deploy/`, cron `/etc/cron.d/salawat-backup` (tous les jours à 04:00), journal `/var/log/salawat-backup.log`.
- Destination `/var/backups/salawat/` (`root` seulement), rétention 30 jours. Contient `db-*.sql.gz` et `env-*.bak` (clés VAPID, SECRET_KEY).
- Premier essai OK : `db-20261125-122357-695.sql.gz`, 8 Ko, 19 tables. Disque : 88 Go libres.
- Accès SSH : clé temporaire ajoutée puis retirée (accès refusé vérifié, clé détruite en local).

### Non fait
- **Restauration non testée sur la VPS** (testée en local seulement).
- **Pas de copie hors VPS** : sauvegardes sur la même machine. Faire un `rsync` vers le poste (à lancer par l'utilisateur) ou activer les snapshots Hostinger dans hPanel. Conserver les copies chiffrées.
- **Portail `dimatlas` non sauvegardé** : scripts `backup-portail.sh` / `restore-portail.sh` prêts (BACKUP.md §6) mais non installés, car ce projet ne doit pas être touché sans accord explicite. Non testés sur le portail.
- Pas de chiffrement des sauvegardes sur la VPS (droits `root` uniquement).

## Ramadan (en ligne depuis le 2026-11-25)
- Entrée de menu **Ramadan** (`/ramadan`) et onglet « Spécial Ramadan » du Calendrier : horaires jour par jour (Imsak, rupture = Maghrib), dates clés (nuit du Destin = soir du 26e jour, nuits impaires, Aïd). Endpoint `/api/v1/prayer-times/ramadan/` (Aladhan `hijriCalendar`, cache 7 jours, copie de secours 60 jours).
- **Rappels Imsak / rupture** par notification : désactivés par défaut, activés dans Réglages (« Rappels de Ramadan »), seulement pendant le mois hégirien 9, ignorent les heures calmes. Migration `0005_ramadan_reminders`.
- Non testé sur téléphone. Prochain Ramadan : 8 février 2027 (±1 jour selon la lune).

## Adhan
- 8 sons en ligne : Abdul Basit (complet et Fajr), Alafasy, Minshawi, La Mecque, Médine, Al-Aqsa, Égypte. « Sonnerie complète » joue Abdul Basit par défaut.
- Source archive.org « adhan_202606 », **sans licence indiquée** : à confirmer avant une diffusion large. Muezzins des nouveaux fichiers non identifiés.
- Le son ne se joue que si l'application est ouverte (limite des navigateurs).

## Coran : statuts, favoris, phonétique (2026-11-26)
- **Statuts de sourate** (À lire, En cours, Lu, À relire / Favori, En apprentissage, Mémorisé, À réviser) et **récitateurs favoris** : store Pinia `readingStatus` (`frontend/src/stores/readingStatus.js`), persistés dans le `localStorage` (`pc_surah_status`, `pc_fav_reciters`). Aucun changement d'API : non synchronisé entre appareils. Les favoris du Coran sont préfixés `quran:` pour ne pas se mêler à ceux des sons d'Adhan.
- **Tri des favoris figé au chargement** : un tri en direct déplaçait les boutons radio au clic et faisait changer le récitateur sélectionné. Comportement voulu : le favori remonte en tête à la prochaine ouverture de la page, pas au clic.
- **Phonétique** : construite côté client depuis `words[].transliteration` (Quran.com, `words=true`), marqueur de fin de verset exclu. Activer la phonétique charge donc les mots de chaque verset (requête plus lourde). Interrupteurs Traduction / Phonétique mémorisés (`pc_show_translation`, `pc_show_phonetic`).
- Ancienne version servie par la PWA : après un déploiement, un rechargement forcé ou deux ouvertures de l'app sont nécessaires pour voir les changements.

## Documentation
- `docs/architecture.html` : page autonome (Vue 3 via cdnjs) sur la stack, la VPS, les conteneurs et le périmètre fonctionnel. Doit être mise à jour si l'architecture change.
- Commandes de déploiement : `django@dimatlas.com` (au lieu de `root@IP`) dans DEPLOY.md, HANDOFF.md, BACKUP.md, TODO.md. `DEPLOYMENT.md` (installation initiale d'une VPS neuve) garde `root`.

## Accès SSH et déploiement
- Procédure : clé temporaire `claude-deploy-salawat` ajoutée puis retirée à chaque déploiement (DEPLOY.md §10).
- La clé `claude-deploy-dimatlas-vps` est **toujours autorisée** sur la VPS (root) : elle ne vient pas de cette session ; à retirer si elle ne sert plus.

## Texte du Coran en base locale (branche `dev_texte_QURAN_local`, 2026-11-27)
- **Principe :** sourates, versets (arabe Uthmani), traductions `fr` (Hamidullah, id 31) et `en` (Saheeh, id 20) et commentaire arabe `ar` (tafsir al-Muyassar, id 16) sont copiés en base (`Surah`, `Verse`, `VerseTranslation`, migration `0002_quran_text`). Les vues lisent la base d'abord (`services/local_text.py`) et gardent le format de réponse de Quran.com : le frontend ne change pas.
- **Repli automatique sur Quran.com** (cache 24 h) si la base est vide, si une sourate est incomplète, si une traduction demandée manque pour un verset, ou si la langue n'est pas importée (autre que `fr`, `en`, `ar`, ou ID numérique). `QURAN_LOCAL_TEXT_ENABLED=false` force ce repli.
- **Import :** `python manage.py import_quran_text` (≈ 1 min, une requête Quran.com par sourate, idempotent). Options : `--translations fr`, `--surah N` (répétable), `--reset`. Une sourate dont le nombre de versets reçu ne correspond pas est refusée sans rien écrire. **Pas automatique** : à lancer une fois après `migrate` (DEPLOY.md §3.4), sinon l'API continue d'appeler Quran.com.
- **Mesuré en local (SQLite) :** 114 sourates, 6 236 versets, 6 236 traductions par langue ; base complète ≈ 4,4 Mo. Les 114 sourates (`fr,en`) sont identiques aux réponses de Quran.com après alignement de l'ordre. Latence : versets ≈ 5–12 ms (contre ≈ 40–55 ms via l'API) ; liste des sourates ≈ 1,3 ms une fois chaud (le premier appel, ≈ 80 ms, est un coût de démarrage, pas celui de la requête). Chiffres indicatifs, un seul passage.
- **Arabe (`ar`) = tafsir, pas une traduction :** Quran.com n'a aucune traduction arabe (126 ressources vérifiées) ; l'ancien « ar = 2 (Simplified Arabic) » du code était faux et ne renvoyait rien. L'arabe vient de `/tafsirs/16/by_chapter/N` (التفسير الميسر), balises HTML retirées. Ce tafsir regroupe parfois des versets (ex. 4:66 couvre 4:66-68) : un verset sans entrée reprend le commentaire du groupe (dans l'import comme dans l'API, pour rester identiques). Vérifié : 114 sourates, 6 236 versets, `fr,en,ar` identiques à l'API, 0 texte vide, 0 balise restante. Le frontend ne propose que fr/en (`SurahView.vue`) : `ar` n'est pas encore affiché. Taille de la base SQLite de dev avec les 3 langues ≈ 7,5 Mo. Licence du tafsir à vérifier.
- **Ordre des traductions :** triées par `resource_id` croissant (ar 16, en 20, fr 31), comme Quran.com, quel que soit l'ordre demandé. Le frontend les affiche dans l'ordre reçu : ne pas changer sans vérifier `VerseList.vue`.
- **Reste externe :** mot à mot, audio, horodatages de suivi (`chapter_recitations?segments=true`). `fetch_chapter_audio` n'est pas mis en cache : chaque lancement d'un récitateur Quran.com refait un appel externe (le front gère le 429).
- **Licences à vérifier** avant de redistribuer les traductions (Hamidullah, Saheeh). Non vérifié.
- **Admin Django :** `Surah`, `Verse`, `VerseTranslation` sont visibles dans `/admin/` en **lecture seule** (ajout, modification, suppression désactivés) pour ne jamais altérer le texte à la main. Ils n'apparaissaient pas tant que `apps/quran/admin.py` n'existait pas ; après un `git pull`, lancer aussi `migrate` puis relancer le serveur.
- **Tests :** `apps/quran/tests/test_local_text.py` (import, lecture sans appel réseau, repli). Suite complète : 191 verts. Pas de venv dans le dépôt (voir HANDOFF.md) ; en dev sans `DB_HOST`, la base est `backend/db.sqlite3` (ignorée par git).
- **À vérifier :** comment le serveur de dev du frontend atteint l'API (pas de `proxy` dans `vite.config.js`). `backend/manage.py` apparaît modifié (droit d'exécution 644 → 755), non committé volontairement.
- **Documentation :** `docs/ARCHITECTURE_CORAN.md` décrit l'architecture du module Coran.

## Bibliothèque (Douâa & Hadiths)
- La base de production était vide (page « Aucune entrée dans cette catégorie »). `seed_library` lancé le 2026-11-25 : 19 douâas + 19 hadiths. Commande idempotente ; à relancer après toute mise à jour de `apps/library/content.py` (jamais `--reset` sans nécessité). Étape désormais documentée dans DEPLOY.md (§3.4, §5, §6, check-list) : elle n'est pas automatique, un nouveau déploiement from scratch affichera une page vide tant qu'elle n'est pas lancée.

## Menu principal
- 7 liens (Horaires, Coran, Outils, Calendrier, Ramadan, Douâa & Hadiths, Réglages) : la barre ne tenait plus sur une ligne en dessous de ~1200 px et « Douâa & Hadiths » était coupé. Corrigé le 2026-11-25 (`navbar-expand-xl` : burger sous 1200 px). Si un lien est ajouté, revérifier la largeur.

## Tests
- Les e2e du Ramadan (onglet, menu) et de l'Adhan passent en local ; test « méthode/madhhab » corrigé (le stockage n'est plus vidé à chaque navigation). Penser à `migrate` sur la base locale après chaque nouvelle migration, sinon les réglages restent en chargement.

## Autres points ouverts
- Compte administrateur Django : à créer par l'utilisateur (`createsuperuser`, voir DEPLOY.md).
- Quran Foundation : adapter l'authentification avant d'y mettre des identifiants.
- Hssain : MP3 non déployés, donc masqué ; Benmoussa limité aux sourates 100–114 (rien d'autre n'est hébergé ; droits de diffusion et riwaya « Hafs » à vérifier).
- Notifications push (Adhan, bip, vibreur, rappels Ramadan) : jamais testées de bout en bout sur un téléphone.
- CPU à 98 % : cause probable = analyse Monarx, non confirmée.
- Limites de requêtes : 1500/h anonyme, 5000/h compte (variables `THROTTLE_ANON` / `THROTTLE_USER`).

Voir aussi : TODO.md, BACKUP.md, DEPLOY.md.
