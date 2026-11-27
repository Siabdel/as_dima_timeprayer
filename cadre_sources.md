# Cadre des sources — Prière & Coran (Salawat)

Document de référence : quelles sources l'application utilise, lesquelles font autorité pour un
utilisateur du Maroc (rite malikite), et comment on le vérifie.
Dernière vérification : **2026-11-27**. Les points non vérifiés sont signalés comme tels.
Les parties marquées **Proposition** sont à valider par le propriétaire du projet.

## 1. Cadre de référence

Le cadre religieux officiel du Maroc est décrit comme l'articulation du **fiqh malikite**, de la
**croyance ashʿarite** et du **soufisme** (voie de Junayd).

- Appuyé par des sources secondaires : [ISD Global](https://www.isdglobal.org/wp-content/uploads/2026/01/Moroccos-Religious-Diplomacy.pdf),
  [MDPI](https://mdpi.com/2077-1444/13/5/392).
- **Non retrouvé dans une source officielle** lors de la vérification : la page d'accueil de
  `habous.gov.ma` (en maintenance au moment de la lecture) et celle de `maroc.ma` ne contiennent
  pas cette formule. Le texte de la Constitution (PDF sur `maroc.ma`) et les discours royaux
  (PDF) **n'ont pas été lus**. Ce point reste à confirmer à la source.
- L'application ne donne **aucun avis juridique (fatwa)** : elle affiche des textes sourcés et des
  calculs. Toute question de rite est renvoyée aux autorités compétentes.

## 2. Hiérarchie des sources par domaine

| Domaine | Source de référence (Maroc) | Source utilisée aujourd'hui | Écart |
|---|---|---|---|
| Texte du Coran | Mushaf Mohammadi, **Warsh ʿan Nāfiʿ** | API Quran.com, **Hafs ʿan ʿĀṣim** | Oui |
| Audio du Coran | Récitations Warsh | Warsh (5 récitateurs « extra » + Hssain masqué) et Hafs (Benmoussa, Quran.com) | Mélange |
| Traductions / tafsir | non défini | Hamidullah (fr), Saheeh International (en), tafsir al-Muyassar (ar), d'origine saoudienne | À décider |
| Hadith | [Plateforme Mohammed VI du Hadith](https://hadithm6.ma) | Cahier de 19 hadiths et 19 douas (Bukhari, Muslim, Abu Dawud, Tirmidhi) | Non recoupé |
| Horaires de prière | Ministère des Habous (seuls ses horaires font foi) | Aladhan, méthode au choix (défaut 3 = MWL) | Défaut à revoir |
| Asr | Ombre = objet (« standard ») | `standard` par défaut | Aucun |
| Fêtes / calendrier | Annonces du Ministère | Non étudié | Hors périmètre vérifié |

## 3. Ce qui a été vérifié

### Texte du Coran
- La base locale contient la lecture de **Hafs** : en 1:4, `مَـٰلِكِ` porte l'alif suscrit (U+0670). Les 14 récitateurs de chapitre de l'API Quran.com sont tous en Hafs.
- Le **Mushaf Mohammadi** est en Warsh ʿan Nāfiʿ. Sources non officielles : [Morocco World News, 2019](https://www.moroccoworldnews.com/2019/04/81493/king-mohammed-vis-moroccanized-quran-to-counter-wahhabism/) (commande royale vers 2010), [Morocco World News, oct. 2026](https://www.moroccoworldnews.com/2026/10/340865/morocco-releases-first-official-amazigh-translation-of-qurans-meanings/) (édition de la Fondation Mohammed VI pour l'édition du Coran, texte en Warsh), [SNRT News, avril 2026](https://snrtnews.com/fr/article/le-ministere-des-habous-et-des-affaires-islamiques-lance-lapplication-le-moushaf-mohammadi) (application numérique « Moushaf Mohammadi » lancée par le Ministère).
- `fm6oa.org` a un lien « المصحف المحمدي » vers `/coran/`, mais la page lue ne contient que son titre (contenu probablement chargé par JavaScript). **Aucune API ni texte numérique réutilisable n'a été trouvé.**
- **Non vérifié :** texte Warsh disponible dans les endpoints Quran.com utilisés ; différences de numérotation des versets.

### Hadith — Plateforme Mohammed VI (`hadithm6.ma`)
- Chargée (HTTP 200). Pied de page : « وزارة الأوقاف و الشؤون الإسلامية ». La page ne se déclare pas « officielle » dans une phrase ; seul ce pied de page nomme le Ministère.
- Recueils couverts (page « شرط المنصة ») : le **Muwatta de Mālik** (riwaya de Yahya ibn Yahya al-Andalusi), Bukhari et Muslim, les quatre Sunan, le Musnad d'Ahmad. Précisions : Bukhari et Muslim passent par le *Jamʿ bayn al-Sahīḥayn* d'Abd al-Ḥaqq al-Ishbīlī (version condensée, pas les textes complets), les quatre Sunan par *Jamʿ al-Fawāʾid* d'al-Rudānī, le Musnad par *Majmaʿ al-Zawāʾid*. La commission dit avoir **écarté certains hadiths** (narrateurs fiables mais contenu jugé problématique).
- Un champ « الحكم » (grade) existe dans la recherche, mais aucune méthode de gradation détaillée n'a été lue.
- **Aucune API, aucun téléchargement, aucune licence de réutilisation trouvés.** Une réutilisation du contenu demande un accord explicite.
- **À faire :** recouper chaque hadith du cahier avec la plateforme (non fait).

### Horaires de prière
- `habous.gov.ma` a une section « مواقيت الصلاة — حسب التوقيت الرسمي للمملكة المغربية (GMT) », mais **sans méthode ni angles** dans le texte lu (le site était en maintenance ; l'URL `/fr/` renvoie 404).
- Des sites tiers (Bladi, Wadifa Public) indiquent la méthode « Maroc — Ministère des Habous » : **Fajr 19°, Isha 17°, Asr standard**, et rappellent que seuls les horaires du Ministère font foi. Un site ajoute des décalages (Chourouq −3 min, Dhuhr +5, Maghrib +5) **non confirmés** par le Ministère.
- Aladhan : méthode 21 « Morocco » = Fajr 19°, Isha 17° (cohérent, vérifié sur `/v1/methods`). Les angles propres au Ministère ne sont **pas confirmés à la source officielle**.

### État des sites cités dans la liste fournie

| Site | Résultat |
|---|---|
| `habous.gov.ma` | Charge (HTTP 200), bandeau « Site en maintenance » ; `/fr/` = 404 |
| `hadithm6.ma` | Charge, lisible |
| `edhh.org` (Dar El Hadith El Hassania) | Charge |
| `fm6oa.org` | Charge ; lien vers le Mushaf Mohammadi, page vide |
| `maroc.ma` | Charge ; aucun texte sur le rite ; Constitution en PDF non lue |
| `daouatalhaq.ma` | **Échec** (connexion refusée) |
| `uaq.ma` | **Échec** (erreur 500) |
| `mapexpress.ma` | **Échec** (403, peut-être un blocage des robots) |

Un échec de lecture ne prouve pas que le site n'existe plus ; il prouve seulement qu'il n'a pas pu être lu ce jour-là.

## 4. Règles proposées (Proposition)

1. **Chaque contenu religieux affiche sa source** (recueil, numéro, ou traducteur et éditeur). Pas de texte sans origine.
2. **Hiérarchie :** source officielle marocaine primaire > source officielle étrangère reconnue > source secondaire. Une source secondaire est marquée comme telle dans la documentation.
3. **La lecture est toujours indiquée** (Hafs ou Warsh) à côté du texte et de chaque récitateur, et le texte affiché doit correspondre à l'audio joué.
4. **Pas de fatwa, pas de rite imposé.** Le rite ne conditionne que ce qui se calcule (méthode d'horaires, Asr).
5. **Licences :** aucune redistribution de traduction, de tafsir ou de contenu de `hadithm6.ma` sans vérification de la licence.
6. **Revérification** de ce document à chaque changement de source, et au moins une fois par an. Les sites officiels changent (le portail des Habous était en maintenance).

## 5. Écarts et actions possibles (non faites)

- Texte Warsh : chercher une source de texte Warsh réutilisable (le Mushaf Mohammadi numérique est une application, pas une API trouvée) ou afficher clairement « texte Hafs ».
- Afficher la lecture (Hafs ou Warsh) à côté de chaque récitateur.
- Méthode 21 par défaut pour un utilisateur marocain (aujourd'hui le défaut de l'API est 3).
- Recouper les 19 hadiths avec `hadithm6.ma` ; envisager le *Muwatta* de Mālik.
- Contacter les Habous pour : angles et décalages officiels des horaires, licence du Mushaf Mohammadi numérique, et réutilisation de `hadithm6.ma`.
- Lire le PDF de la Constitution et les discours royaux pour sourcer le cadre du §1.

## 6. Points des textes fournis non confirmés

La liste de sites et la description du cadre fournies pour cette recherche contiennent des affirmations que la vérification n'a **pas** confirmées :
- « `habous.gov.ma` définit… (rite malikite, croyance ashʿarite) » : cette formule n'apparaît pas sur la page d'accueil lue.
- « Des discours royaux et des communications du site `maroc.ma` réaffirment… l'unité du rite malikite sunnite » : non retrouvé ; les discours n'ont pas été lus.
- `daouatalhaq.ma`, `uaq.ma` et `mapexpress.ma` : illisibles ce jour-là (voir §3).
- « Conseil Supérieur des Oulémas hébergé sur `habous.gov.ma` » : la page d'accueil mentionne un « المجلس العلمي الأعلى » (Conseil scientifique supérieur), sans page dédiée lue.
- « `chabab.ma` associé à la Rabita Mohammadia » : non vérifié.
