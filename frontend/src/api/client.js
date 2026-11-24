// Client HTTP Axios centralisé pour l'API v1 du backend.
// - baseURL configurable via VITE_API_BASE_URL (aucun secret en dur) ;
// - tokens JWT persistés dans le localStorage (clé « pc_tokens ») ;
// - refresh token automatique UNE SEULE FOIS en cas de 401, avec une
//   promesse partagée pour éviter les rafraîchissements en cascade.
import axios from 'axios';

// URL de base de l'API (peut être surchargée au build ou au runtime Vite).
export const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

const TOKENS_KEY = 'pc_tokens';

/**
 * Retourne les tokens stockés ({ access, refresh }) ou null.
 * @returns {{ access: string, refresh: string } | null}
 */
export function getTokens() {
  try {
    const raw = window.localStorage.getItem(TOKENS_KEY);
    return raw ? JSON.parse(raw) : null;
  } catch {
    // JSON invalide ou localStorage indisponible : on considère déconnecté.
    return null;
  }
}

/**
 * Persiste les tokens dans le localStorage.
 * @param {{ access: string, refresh: string }} tokens
 */
export function setTokens(tokens) {
  window.localStorage.setItem(TOKENS_KEY, JSON.stringify(tokens));
}

/**
 * Supprime les tokens du localStorage (déconnexion ou refresh impossible).
 */
export function clearTokens() {
  window.localStorage.removeItem(TOKENS_KEY);
}

const client = axios.create({
  baseURL: API_BASE_URL,
  headers: { 'Content-Type': 'application/json' },
});

// Intercepteur requête : ajoute le header Authorization si un access token existe.
client.interceptors.request.use((config) => {
  const tokens = getTokens();
  if (tokens?.access) {
    config.headers.Authorization = `Bearer ${tokens.access}`;
  }
  return config;
});

// Promesse partagée : plusieurs 401 simultanés ne déclenchent qu'un seul refresh.
let refreshPromise = null;

/**
 * Demande une nouvelle paire de tokens et met à jour le localStorage.
 * @param {string} refresh Refresh token encore valide
 * @returns {Promise<{ access: string, refresh: string }>}
 */
function refreshTokens(refresh) {
  if (!refreshPromise) {
    refreshPromise = axios
      .post(`${API_BASE_URL}/auth/token/refresh/`, { refresh })
      .then((response) => {
        setTokens(response.data);
        return response.data;
      })
      .finally(() => {
        // La promesse est consommée : un futur refresh redevient possible.
        refreshPromise = null;
      });
  }
  return refreshPromise;
}

// Intercepteur réponse : sur 401, tente un unique refresh puis rejoue la requête.
client.interceptors.response.use(
  (response) => response,
  async (error) => {
    const original = error.config;

    // Pas de réponse HTTP (réseau, CORS, ...) : rien à rafraîchir.
    if (!error.response || !original) {
      return Promise.reject(error);
    }

    const tokens = getTokens();
    const url = original.url || '';
    // Jamais de refresh sur l'endpoint de refresh lui-même (évite une boucle).
    const isRefreshCall = url.includes('/auth/token/refresh/');

    if (
      error.response.status === 401 &&
      !original._retry &&
      tokens?.refresh &&
      !isRefreshCall
    ) {
      original._retry = true;
      try {
        await refreshTokens(tokens.refresh);
        // Rejoue la requête initiale : l'intercepteur requête ajoutera
        // le nouvel access token automatiquement.
        return client(original);
      } catch {
        // Refresh impossible : purge locale + notification globale de déconnexion.
        clearTokens();
        window.dispatchEvent(new CustomEvent('auth:logout'));
        return Promise.reject(error);
      }
    }

    return Promise.reject(error);
  }
);

export default client;
