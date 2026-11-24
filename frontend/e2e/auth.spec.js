/**
 * Tests E2E — Authentification (étape 1).
 * Couvre : inscription via l'UI, connexion, déconnexion, garde de route
 * protégée, et les erreurs de connexion.
 */
import { test, expect } from '@playwright/test';
import { createUser } from './helpers.js';

test.describe('Authentification', () => {
  test("s'inscrire puis être connecté et redirigé vers l'accueil", async ({ page }) => {
    // Compte unique par exécution pour éviter les collisions d'e-mail.
    const email = `e2e-ui-${Date.now()}@test.local`;
    const password = 'UnMotDePasseSolide1!';

    await page.goto('/register');
    await expect(page.getByRole('heading', { name: 'Créer un compte' })).toBeVisible();

    await page.fill('#register-email', email);
    await page.fill('#register-first-name', 'E2E');
    await page.fill('#register-last-name', 'Testeur');
    await page.fill('#register-password', password);
    await page.fill('#register-password2', password);

    await page.getByRole('button', { name: 'Créer mon compte' }).click();

    // Redirection vers l'accueil + e-mail visible dans la navbar.
    await expect(page).toHaveURL(/\/$/);
    await expect(page.getByText(email)).toBeVisible();
    await expect(page.getByRole('button', { name: 'Déconnexion' })).toBeVisible();
  });

  test('refuser un mot de passe non conforme (confirmation différente)', async ({ page }) => {
    const email = `e2e-bad-${Date.now()}@test.local`;
    await page.goto('/register');
    await page.fill('#register-email', email);
    await page.fill('#register-password', 'UnMotDePasseSolide1!');
    await page.fill('#register-password2', 'UnAutreMotDePasse1!');
    await page.getByRole('button', { name: 'Créer mon compte' }).click();

    // Le backend renvoie 400 : erreur de validation affichée côté UI.
    await expect(page).toHaveURL(/\/register/);
    await expect(page.getByText(/mot de passe|correspond/i).first()).toBeVisible();
  });

  test('se connecter avec un compte existant', async ({ page, request }) => {
    const { email, password } = await createUser(request);

    await page.goto('/login');
    await page.fill('#login-email', email);
    await page.fill('#login-password', password);
    await page.getByRole('button', { name: 'Se connecter' }).click();

    await expect(page).toHaveURL(/\/$/);
    await expect(page.getByText(email)).toBeVisible();
  });

  test('afficher une erreur pour de mauvais identifiants', async ({ page }) => {
    await page.goto('/login');
    await page.fill('#login-email', 'inconnu@test.local');
    await page.fill('#login-password', 'MauvaisMotDePasse1!');
    await page.getByRole('button', { name: 'Se connecter' }).click();

    await expect(page.getByRole('alert')).toBeVisible();
    await expect(page).toHaveURL(/\/login/);
  });

  test('se déconnecter', async ({ page, request }) => {
    const { email, password } = await createUser(request);

    // Connexion via l'UI (parcours complet une fois).
    await page.goto('/login');
    await page.fill('#login-email', email);
    await page.fill('#login-password', password);
    await page.getByRole('button', { name: 'Se connecter' }).click();
    await expect(page.getByRole('button', { name: 'Déconnexion' })).toBeVisible();

    await page.getByRole('button', { name: 'Déconnexion' }).click();

    // La navbar repasse en mode visiteur.
    await expect(page.getByRole('link', { name: 'Connexion' })).toBeVisible();
    await expect(page.getByText(email)).toBeHidden();
  });

  test('/settings est ouverte aux invités : sections locales + invitation à se connecter', async ({ page }) => {
    await page.goto('/settings');
    await expect(page).toHaveURL(/\/settings/);
    await expect(page.getByText('Connectez-vous pour enregistrer vos préférences')).toBeVisible();
    await expect(page.getByRole('heading', { name: 'Ma position' })).toBeVisible();
    await expect(page.getByRole('heading', { name: 'Audio et récitation du Coran' })).toBeVisible();
    // Sections de compte masquées.
    await expect(page.getByRole('heading', { name: 'Préférences de notification' })).toBeHidden();
  });
});
