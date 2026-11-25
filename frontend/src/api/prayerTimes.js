// ===========================================================================
// Appels API « horaires de prière » — contrat backend /api/v1/prayer-times/.
// ===========================================================================
import client from './client';

/**
 * GET /prayer-times/ — horaires pour un lieu et une date donnés.
 * @param {Object} params
 *   - { latitude, longitude } OU { city, country }
 *   - date (optionnel, « YYYY-MM-DD », défaut aujourd'hui)
 *   - method (0-30, défaut 3), madhhab (« standard » | « hanafi »)
 * @returns {Promise<Object>} réponse du backend (timings, hijri_date, ...)
 */
export function getPrayerTimes(params = {}) {
  return client.get('/prayer-times/', { params });
}

/**
 * GET /prayer-times/today/ — horaires du jour pour le lieu par défaut
 * de l'utilisateur connecté (400 « no_default_location » sinon).
 * @param {Object} params { method, madhhab }
 * @returns {Promise<Object>}
 */
export function getTodayPrayerTimes(params = {}) {
  return client.get('/prayer-times/today/', { params });
}

/**
 * GET /prayer-times/ramadan/ — horaires de chaque jour de Ramadan + dates clés.
 * @param {Object} params { latitude, longitude, method, madhhab, hijri_year? }
 */
export function getRamadanCalendar(params = {}) {
  return client.get('/prayer-times/ramadan/', { params });
}
