// ===========================================================================
// Utilitaires de temps pour les horaires de prière.
// ---------------------------------------------------------------------------
// Toutes les fonctions travaillent en « secondes depuis minuit » dans la
// timezone du lieu (et non celle du navigateur), via Intl.DateTimeFormat.
// ===========================================================================

/** Ordre chronologique des prières dans une journée. */
export const PRAYER_ORDER = ['fajr', 'sunrise', 'dhuhr', 'asr', 'maghrib', 'isha'];

/**
 * Convertit une heure « HH:MM » en secondes depuis minuit.
 * @param {string} time
 * @returns {number}
 */
export function timeToSeconds(time) {
  if (!time || typeof time !== 'string') return null;
  const [hours, minutes] = time.split(':').map(Number);
  if (Number.isNaN(hours) || Number.isNaN(minutes)) return null;
  return hours * 3600 + minutes * 60;
}

/**
 * Formate la date hégirienne renvoyée par l'API en texte lisible :
 * « 10 Joumada al-Oula 1446 » (jour + mois + année).
 * @param {{ day: string, month: { name: string }, year: string } | null} hijriDate
 * @returns {string}
 */
export function formatHijri(hijriDate) {
  if (!hijriDate?.month?.name) return '';
  const day = hijriDate.day ?? '';
  const year = hijriDate.year ?? '';
  return `${day} ${hijriDate.month.name} ${year}`.trim();
}

/**
 * Heure courante DANS la timezone du lieu, sous forme d'objets simples.
 * Utilise Intl.DateTimeFormat('en-GB') (format 24 h fixe) puis parse les
 * composantes : indépendant du fuseau du navigateur.
 * @param {string | null} timezone ex. « Europe/Paris »
 * @returns {{ hours: number, minutes: number, seconds: number }}
 */
export function localNowInTimezone(timezone) {
  try {
    if (!timezone) throw new Error('timezone manquante');
    const formatter = new Intl.DateTimeFormat('en-GB', {
      timeZone: timezone,
      hour12: false,
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
    });
    const parts = formatter.formatToParts(new Date());
    const value = (type) => Number(parts.find((p) => p.type === type)?.value ?? 0);
    const hours = value('hour');
    // Certains environnements renvoient « 24 » pour minuit en format 24 h.
    return {
      hours: hours === 24 ? 0 : hours,
      minutes: value('minute'),
      seconds: value('second'),
    };
  } catch {
    // Timezone invalide ou Intl indisponible : repli sur l'heure locale
    // du navigateur (cas du lieu dans le même fuseau).
    const now = new Date();
    return {
      hours: now.getHours(),
      minutes: now.getMinutes(),
      seconds: now.getSeconds(),
    };
  }
}

/**
 * Prochaine prière à venir par rapport à l'heure ACTUELLE DU LIEU.
 * @param {Object | null} timings objet { fajr, sunrise, dhuhr, asr, maghrib, isha }
 * @param {string | null} timezone
 * @returns {{ name: string, time: string } | null} null si toutes les prières
 *          du jour sont passées (après Isha).
 */
export function getNextPrayer(timings, timezone) {
  if (!timings) return null;
  const now = localNowInTimezone(timezone);
  const nowSeconds = now.hours * 3600 + now.minutes * 60 + now.seconds;
  for (const name of PRAYER_ORDER) {
    const seconds = timeToSeconds(timings[name]);
    if (seconds == null) continue;
    if (seconds > nowSeconds) {
      return { name, time: timings[name] };
    }
  }
  return null;
}

/**
 * Temps restant avant la prochaine prière, exprimé en h/m/s.
 * @param {Object | null} timings
 * @param {string | null} timezone
 * @returns {{ hours: number, minutes: number, seconds: number } | null}
 */
export function timeUntilNextPrayer(timings, timezone) {
  const next = getNextPrayer(timings, timezone);
  if (!next) return null;
  const now = localNowInTimezone(timezone);
  const nowSeconds = now.hours * 3600 + now.minutes * 60 + now.seconds;
  const diff = Math.max(0, timeToSeconds(next.time) - nowSeconds);
  return {
    hours: Math.floor(diff / 3600),
    minutes: Math.floor((diff % 3600) / 60),
    seconds: diff % 60,
  };
}
