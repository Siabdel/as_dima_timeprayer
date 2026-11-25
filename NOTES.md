# Notes d'exploitation — Prière & Coran (Salawat)

Remarques de suivi, mises à jour le 2026-11-25.

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

## Autres points ouverts
- Compte administrateur Django : à créer par l'utilisateur (`createsuperuser`, voir DEPLOY.md).
- Quran Foundation : adapter l'authentification avant d'y mettre des identifiants.
- Hssain : MP3 non déployés, donc masqué ; Benmoussa limité aux sourates 100–114 (rien d'autre n'est hébergé ; droits de diffusion et riwaya « Hafs » à vérifier).
- Notifications push : jamais testées de bout en bout sur un téléphone.
- CPU à 98 % : cause probable = analyse Monarx, non confirmée.
- Limites de requêtes : 1500/h anonyme, 5000/h compte (variables `THROTTLE_ANON` / `THROTTLE_USER`).

Voir aussi : TODO.md, BACKUP.md, DEPLOY.md.
