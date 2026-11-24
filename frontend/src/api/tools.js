// ===========================================================================
// Appels API « Outils & notifications » — contrat backend /api/v1/.
// ---------------------------------------------------------------------------
// Endpoints :
//   - GET  /qibla/?lat=&lng=              → cap vers La Mecque (public)
//   - GET  /hijri/?date=YYYY-MM-DD        → date hégirienne (public, défaut : aujourd'hui)
//   - GET    /notifications/vapid-key/    → clé publique VAPID (public)
//   - POST   /notifications/subscribe/    → enregistre l'abonnement push (JWT)
//   - DELETE /notifications/subscribe/    → supprime l'abonnement push (JWT)
//   - GET    /notifications/status/       → état de l'abonnement (JWT)
//   - POST   /notifications/test/         → notification de test (JWT, throttle 5/h)
//
// REMARQUE ROUTAGE : le backend monte les vues « tools » à la racine de
// /api/v1/ (config/api_router.py → path("", include("apps.tools.urls"))),
// soit /api/v1/qibla/ et /api/v1/hijri/ — et NON /api/v1/tools/qibla/.
// Les chemins ci-dessous sont donc relatifs à la base de l'API.
// ===========================================================================
import client from './client';

/**
 * GET /qibla/ — cap vers la Kaaba depuis des coordonnées.
 * @param {number|string} lat latitude décimale (-90..90)
 * @param {number|string} lng longitude décimale (-180..180)
 * @returns {Promise<Object>} { qibla_direction, compass_point, kaaba_distance_km }
 */
export function getQibla(lat, lng) {
  return client.get('/qibla/', { params: { lat, lng } });
}

/**
 * GET /hijri/ — conversion grégorien → hégirien (calendrier Umm al-Qura).
 * @param {string} [date] date « YYYY-MM-DD » (défaut : aujourd'hui côté serveur)
 * @returns {Promise<Object>} { gregorian_date, hijri_date: { day, year,
 *   month: { number, name, name_ar } } }
 */
export function getHijri(date = null) {
  return client.get('/hijri/', { params: date ? { date } : {} });
}

/**
 * GET /notifications/vapid-key/ — clé publique VAPID pour pushManager.subscribe.
 * @returns {Promise<Object>} { public_key }
 */
export function getVapidKey() {
  return client.get('/notifications/vapid-key/');
}

/**
 * POST /notifications/subscribe/ — enregistre (ou renouvelle) l'abonnement
 * Web Push de l'utilisateur connecté (upsert idempotent par endpoint).
 * @param {{ endpoint: string, keys: { p256dh: string, auth: string },
 *           user_agent?: string }} payload
 * @returns {Promise<Object>} { status: 'subscribed', endpoint }
 */
export function subscribePush(payload) {
  return client.post('/notifications/subscribe/', payload);
}

/**
 * DELETE /notifications/subscribe/ — supprime l'abonnement correspondant à
 * l'endpoint (le corps est transmis via l'option `data` d'Axios).
 * @param {string} endpoint URL de l'abonnement push
 * @returns {Promise<Object>} { status: 'unsubscribed', deleted: n }
 */
export function unsubscribePush(endpoint) {
  return client.delete('/notifications/subscribe/', { data: { endpoint } });
}

/**
 * GET /notifications/status/ — état de l'abonnement push de l'utilisateur
 * connecté + dernières notifications envoyées.
 * @returns {Promise<Object>} { subscribed, subscriptions_count,
 *   recent_notifications: [{ prayer, date, status, sent_at }] }
 */
export function getSubscriptionStatus() {
  return client.get('/notifications/status/');
}

/**
 * POST /notifications/test/ — envoie une notification de test pour une prière
 * (JWT requis, limité à 5 envois/heure ; 400 « no_subscription » si aucun
 * abonnement enregistré).
 * @param {string} prayerName « fajr|sunrise|dhuhr|asr|maghrib|isha »
 * @returns {Promise<Object>} { status: 'sent', sent, removed }
 */
export function sendTestNotification(prayerName) {
  return client.post('/notifications/test/', { prayer_name: prayerName });
}
