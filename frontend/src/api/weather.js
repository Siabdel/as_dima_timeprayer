// GET /weather/ — météo du lieu (public, mise en cache serveur 15 min).
// Paramètres : { latitude, longitude, city? } ou { city, country? }.
import client from './client';

/**
 * @param {Object} params
 * @returns {Promise<Object>} { location, timezone, current, hourly, daily }
 */
export function getWeather(params) {
  return client.get('/weather/', { params });
}
