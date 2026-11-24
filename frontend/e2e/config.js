/**
 * Configuration centrale des tests E2E (URL de base de l'API, timeouts).
 * Aucun secret ici : l'API est locale et ne contient pas de données sensibles.
 */
export const API_BASE_URL =
  process.env.E2E_API_BASE_URL || 'http://localhost:8000/api/v1';

export const TIMEOUTS = {
  navigation: 15_000,
  api: 15_000,
};
