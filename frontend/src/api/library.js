// ===========================================================================
// Appels API « bibliothèque » (douâas + hadiths) — contrat backend
// /api/v1/library/. Endpoints publics, paginés côté backend (page size 20).
// ===========================================================================
import client from './client';

/**
 * GET /library/categories/ — catégories disponibles pour les douâas et les
 * hadiths. @returns {Promise<Object>} { duas: [{key,label}], hadiths: [...] }
 */
export function getCategories() {
  return client.get('/library/categories/');
}

/**
 * GET /library/categories/ — catégories des douâas uniquement.
 * @returns {Promise<Object>} { duas: [{key,label}], hadiths: [...] }
 */
export function getDuaCategories() {
  return client.get('/library/categories/');
}

/**
 * GET /library/categories/ — catégories des hadiths uniquement.
 * @returns {Promise<Object>} { duas: [{key,label}], hadiths: [...] }
 */
export function getHadithCategories() {
  return client.get('/library/categories/');
}

/**
 * GET /library/duas/ — liste paginée des douâas (filtre ?category= optionnel).
 * @param {string} [category] Clé de catégorie (ex. « repas ») ; omis si vide.
 * @returns {Promise<Object>} { count, next, previous, results }
 */
export function getDuas(category) {
  const params = {};
  if (category) params.category = category;
  return client.get('/library/duas/', { params });
}

/**
 * GET /library/hadiths/ — liste paginée des hadiths (filtre ?category=
 * optionnel). @param {string} [category] Clé de catégorie (ex. « foi »).
 * @returns {Promise<Object>} { count, next, previous, results }
 */
export function getHadiths(category) {
  const params = {};
  if (category) params.category = category;
  return client.get('/library/hadiths/', { params });
}
