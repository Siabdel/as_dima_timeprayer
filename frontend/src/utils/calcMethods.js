// ===========================================================================
// Méthodes de calcul des horaires de prière (identifiants Aladhan) et
// organismes de référence suggérés par pays.
// ===========================================================================

/** Méthodes proposées (contrat API : entier 0-30, défaut 3). */
export const CALC_METHODS = [
  { value: 3, label: 'Ligue Islamique Mondiale (MWL)' },
  { value: 12, label: 'UOIF — Union des Organisations Islamiques de France' },
  { value: 21, label: 'Ministère des Habous et des Affaires islamiques (Maroc)' },
  { value: 4, label: 'Umm al-Qura (La Mecque)' },
  { value: 19, label: 'Algérie — Ministère des Affaires religieuses' },
  { value: 18, label: 'Tunisie — Ministère des Affaires religieuses' },
  { value: 5, label: 'Autorité générale égyptienne' },
  { value: 13, label: 'Diyanet (Turquie)' },
  { value: 2, label: 'ISNA (Amérique du Nord)' },
  { value: 1, label: 'Université des sciences islamiques, Karachi' },
  { value: 23, label: 'Jordanie — Ministère des Awqaf' },
  { value: 14, label: 'Administration spirituelle des musulmans de Russie' },
  { value: 0, label: 'Shia Ithna-Ashari (Jafari)' },
];

/**
 * Pays → méthode recommandée (code ISO 3166-1 alpha-2). Suggestion
 * uniquement : l'utilisateur garde la main.
 */
export const COUNTRY_METHODS = [
  { code: 'FR', label: 'France', method: 12 },
  { code: 'MA', label: 'Maroc', method: 21 },
  { code: 'DZ', label: 'Algérie', method: 19 },
  { code: 'TN', label: 'Tunisie', method: 18 },
  { code: 'EG', label: 'Égypte', method: 5 },
  { code: 'SA', label: 'Arabie saoudite', method: 4 },
  { code: 'TR', label: 'Turquie', method: 13 },
  { code: 'JO', label: 'Jordanie', method: 23 },
  { code: 'RU', label: 'Russie', method: 14 },
  { code: 'US', label: 'États-Unis / Canada', method: 2 },
  { code: 'PK', label: 'Pakistan', method: 1 },
  { code: 'BE', label: 'Belgique', method: 3 },
  { code: 'GB', label: 'Royaume-Uni', method: 3 },
];

/** Fuseaux courants proposés en tête de liste. */
export const COMMON_TIMEZONES = [
  'Europe/Paris',
  'Africa/Casablanca',
  'Africa/Algiers',
  'Africa/Tunis',
  'Africa/Cairo',
  'Europe/London',
  'Europe/Brussels',
  'Europe/Istanbul',
  'Asia/Riyadh',
  'America/New_York',
  'America/Montreal',
];

/** Fuseau de l'appareil (nom IANA) ou « UTC » en repli. */
export function deviceTimezone() {
  try {
    return Intl.DateTimeFormat().resolvedOptions().timeZone || 'UTC';
  } catch {
    return 'UTC';
  }
}

/**
 * Décalage UTC actuel d'un fuseau, ex. « UTC+1 », « UTC+0 » — tient compte
 * de l'heure d'été/hiver et des changements de Ramadan (base IANA du navigateur).
 */
export function utcOffsetLabel(timeZone, date = new Date()) {
  try {
    const part = new Intl.DateTimeFormat('en-US', {
      timeZone,
      timeZoneName: 'shortOffset',
    })
      .formatToParts(date)
      .find((p) => p.type === 'timeZoneName')?.value;
    if (!part) return '';
    return part === 'GMT' ? 'UTC+0' : part.replace('GMT', 'UTC');
  } catch {
    return '';
  }
}

/** Tous les fuseaux IANA connus du navigateur (repli : liste courante). */
export function allTimezones() {
  try {
    return Intl.supportedValuesOf('timeZone');
  } catch {
    return COMMON_TIMEZONES;
  }
}
