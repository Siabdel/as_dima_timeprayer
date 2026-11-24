// ===========================================================================
// Appels API « sons d'Adhan » — contrat backend /api/v1/.
// ---------------------------------------------------------------------------
//   GET /notifications/adhan-sounds/ → { sounds: [{ id, name, reciter, url }],
//                                        default: '<id>' }
// Public (donnée statique du catalogue) : utilisable avant connexion.
// ===========================================================================
import client from './client';

/**
 * GET /notifications/adhan-sounds/ — catalogue des sons d'Adhan.
 * @returns {Promise<Object>} { sounds: [{ id, name, reciter, url }], default }
 */
export function getAdhanSounds() {
  return client.get('/notifications/adhan-sounds/');
}
