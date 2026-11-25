# TODO

## À vérifier (non testé dans un navigateur)
- [ ] Suivi verset/mot : tester avec plusieurs récitateurs (certains n'ont peut-être pas de `timestamps`/`segments`).
- [ ] Cache audio : `crossorigin="anonymous"` sur le `<audio>` ; vérifier que chaque hôte audio de récitateur envoie du CORS (sinon repli sans cache).
- [ ] Notifications : mode bip/vibreur, volume, fade-in et Adhan du Fajr, de bout en bout (push réel).
- [ ] Rappel avant l'Adhan (`send_prayer_reminder`) : vérifier la fenêtre de scan (5 min) en conditions réelles.
- [ ] Lancer les tests E2E Playwright (`frontend/e2e`) ; ajouter des scénarios pour le suivi et les nouveaux réglages.

## Migration / données
- [ ] Appliquer la migration `accounts/0004_preferences_settings` en production.
- [ ] Utilisateurs ayant choisi « Maroc » avant la correction (valeur 14 = Russie) : leur faire re-sélectionner la méthode 21, ou migrer 14 → 21.

## Fonctionnalités restantes
- [ ] Interface multilingue (la préférence `language` ne règle aujourd'hui que la traduction du Coran).
- [ ] Qualité audio (kbps) : impossible avec l'API Quran.com actuelle ; envisager une autre source.
- [ ] Muezzins supplémentaires (La Mecque, Médine, Al-Aqsa) : ajouter les mp3 libres de droits dans `frontend/public/adhan/` + `backend/apps/notifications/adhan_sounds.py`.
- [x] Récitateurs marocains Warsh (Qazabri, Al-Kouchi, Benkirane, Lharraz, Belalya) via mp3quran.net (`EXTRA_RECITERS`). Sans horodatages : pas de suivi verset/mot. Le texte affiché reste en Hafs.
- [x] Cheikh Abderrahmane Benmoussa : 114 mp3 locaux dans `frontend/public/quran/benmoussa/` (non versionnés, 816 Mo ; à déployer sur le serveur à part). Catalogue : `backend/apps/quran/local_reciters.py`. À vérifier : la riwaya affichée (« Hafs ») — Benmoussa est connu pour le Warsh ; corriger `riwaya` si besoin.
- [ ] Adhan de Benmoussa : aucun enregistrement fourni.
- [ ] Cheikh Abdelhamid Hssain : aucune source audio libre trouvée.
- [ ] Méthode « Grande Mosquée de Paris » : pas de méthode Aladhan dédiée (UOIF proposée) ; envisager des angles personnalisés.
- [ ] Adhan joué seulement app ouverte (limite navigateur) ; envisager l'app Android (TWA, voir DEPLOYMENT.md partie B) pour un son natif.
- [ ] Fuseau choisi : utilisé pour les heures calmes seulement ; le calcul des horaires suit le fuseau du lieu.

## Météo
- [ ] Libellé du temps pour les jours suivants (l'API n'expose que celui du moment présent).
- [ ] Icônes jour/nuit ; alertes météo.

## Déploiement
- [x] Déployé sur VPS Hostinger : https://salawat.dimatlas.com (voir HANDOFF.md).
- [ ] Publication Play Store via TWA (partie B).
