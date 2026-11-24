/**
 * Helpers partagés entre les tests E2E :
 * - création d'un compte de test via l'API (plus rapide que l'UI) ;
 * - suppression de la donnée de test entre les suites.
 */
import { API_BASE_URL } from './config.js';

// Compteur pour garantir l'unicité des e-mails de test.
let counter = 0;

/**
 * Crée un utilisateur via POST /api/v1/auth/register/ et retourne ses identifiants.
 * @returns {Promise<{email: string, password: string}>}
 */
export async function createUser(apiContext) {
  counter += 1;
  // Suffixe aléatoire : les tests tournent en parallèle (un compteur par
  // worker) — sans lui, deux workers de la même milliseconde génèrent le
  // même e-mail et le second échoue en doublon.
  const email = `e2e-${Date.now()}-${counter}-${Math.random().toString(36).slice(2, 8)}@test.local`;
  const password = 'UnMotDePasseSolide1!';

  const response = await apiContext.post(`${API_BASE_URL}/auth/register/`, {
    data: {
      email,
      password,
      password2: password,
      first_name: 'E2E',
      last_name: 'Testeur',
    },
  });
  if (!response.ok()) {
    throw new Error(`Création d'utilisateur échouée : ${response.status()} ${await response.text()}`);
  }
  return { email, password };
}

/**
 * Récupère un token d'accès JWT via POST /api/v1/auth/token/.
 * @returns {Promise<string>}
 */
export async function getAccessToken(apiContext, email, password) {
  const response = await apiContext.post(`${API_BASE_URL}/auth/token/`, {
    data: { email, password },
  });
  if (!response.ok()) {
    throw new Error(`Connexion échouée : ${response.status()}`);
  }
  return (await response.json()).access;
}

/**
 * Connexion via l'interface (page /login), comme un utilisateur réel.
 * Attend la redirection vers l'accueil avant de rendre la main.
 * @param {import('@playwright/test').Page} page
 * @param {string} email
 * @param {string} password
 */
export async function loginViaUI(page, email, password) {
  await page.goto('/login');
  await page.fill('#login-email', email);
  await page.fill('#login-password', password);
  await page.getByRole('button', { name: 'Se connecter' }).click();
  await page.waitForURL(/\/$/);
}
