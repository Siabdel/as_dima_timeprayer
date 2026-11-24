// Fonctions d'authentification et de préférences utilisateur, basées sur le
// client Axios (intercepteurs gérés dans client.js).
import client from './client';

/**
 * Inscription d'un nouvel utilisateur.
 * Contrat : POST /auth/register/ → 201 { id, email, first_name, last_name }
 * @param {{ email: string, password: string, password2: string,
 *           first_name?: string, last_name?: string }} payload
 */
export function register(payload) {
  return client.post('/auth/register/', payload).then((response) => response.data);
}

/**
 * Connexion : échange email + mot de passe contre une paire de tokens JWT.
 * Contrat : POST /auth/token/ → 200 { access, refresh }
 * @param {string} email
 * @param {string} password
 */
export function login(email, password) {
  return client.post('/auth/token/', { email, password }).then((response) => response.data);
}

/**
 * Profil de l'utilisateur connecté (nécessite un access token valide).
 * Contrat : GET /auth/me/ → { id, email, first_name, last_name }
 */
export function me() {
  return client.get('/auth/me/').then((response) => response.data);
}

/**
 * Mise à jour des préférences de notification de l'utilisateur connecté.
 * Contrat : PUT /auth/preferences/ → préférences après mise à jour
 * @param {object} payload Préférences partielles ou complètes
 */
export function updatePreferences(payload) {
  return client.put('/auth/preferences/', payload).then((response) => response.data);
}
