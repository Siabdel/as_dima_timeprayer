// ===========================================================================
// Appels API « calendrier des fêtes » — contrat backend /api/v1/events/.
// ===========================================================================
import client from './client';

/**
 * GET /events/?year=YYYY — fêtes (islamiques + nationales) d'une année
 * grégorienne, triées par date croissante.
 * @param {number|string} year Année grégorienne (ex. 2026)
 * @returns {Promise<Object>} { year, hijri_years, count, events }
 */
export function getYearEvents(year) {
  return client.get('/events/', { params: { year } });
}

/**
 * GET /events/upcoming/?limit=N — prochains événements à partir d'aujourd'hui
 * (champ days_until ajouté par le backend).
 * @param {number} [limit=12] Nombre d'événements à retourner
 * @returns {Promise<Object>} { today, count, events }
 */
export function getUpcomingEvents(limit = 12) {
  return client.get('/events/upcoming/', { params: { limit } });
}

/**
 * GET /events/hijri-year/?year=YYYY — fêtes islamiques d'une année hégirienne.
 * @param {number|string} year Année hégirienne (ex. 1448)
 * @returns {Promise<Object>} { hijri_year, count, events }
 */
export function getHijriYearEvents(year) {
  return client.get('/events/hijri-year/', { params: { year } });
}

/**
 * GET /events/france/?year=YYYY — jours fériés en France d'une année.
 * @param {number|string} year Année grégorienne
 * @returns {Promise<Object>} { year, count, holidays: [{ id, name, date, description, regional }] }
 */
export function getFranceHolidays(year) {
  return client.get('/events/france/', { params: { year } });
}
