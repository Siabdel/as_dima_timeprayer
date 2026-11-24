/**
 * Tests E2E — Horaires de prière (étape 2).
 * Couvre : écran d'accueil sans lieu, recherche par ville, affichage des
 * horaires et de la date hégirienne.
 */
import { test, expect } from '@playwright/test';

test.describe('Horaires de prière', () => {
  test("afficher l'écran « Choisissez votre lieu » pour un visiteur", async ({ page }) => {
    await page.addInitScript(() => window.localStorage.clear());
    await page.goto('/');

    await expect(page.getByRole('heading', { name: 'Choisissez votre lieu' })).toBeVisible();
    await expect(page.getByRole('button', { name: /ma position/i })).toBeVisible();
  });

  test('récupérer les horaires via recherche par ville', async ({ page }) => {
    // État propre : le clear se fait via evaluate (une fois), PAS via
    // addInitScript qui s'exécuterait aussi au reload final et effacerait
    // le lieu persisté avant que l'app ne se recharge.
    await page.goto('/');
    await page.evaluate(() => window.localStorage.clear());
    await page.reload();

    // Ouvrir le formulaire ville (bouton « Saisir une ville » / focus sur le champ)
    await page.getByRole('button', { name: /ville/i }).first().click();
    await page.fill('#pc-city', 'Paris');
    await page.fill('#pc-country', 'France');
    await page.locator('form:has(#pc-city)').getByRole('button', { type: 'submit' }).click();

    // Horaires du jour : les 6 prières doivent être visibles (libellés FR).
    await expect(page.getByRole('heading', { name: 'Horaires du jour' })).toBeVisible();
    for (const prayer of ['Fajr', 'Lever du soleil', 'Dhuhr', 'Asr', 'Maghrib', 'Isha']) {
      await expect(page.getByText(prayer, { exact: true }).first()).toBeVisible();
    }

    // Date hégirienne présente (au moins un badge avec l'année 144x ou 1448).
    await expect(page.getByText(/14[4-9][0-9]/).first()).toBeVisible();

    // Le lieu est persisté : rechargement → pas de retour à l'écran d'accueil.
    await page.reload();
    await expect(page.getByRole('heading', { name: 'Horaires du jour' })).toBeVisible();
  });

  test('les sélecteurs méthode et madhhab sont présents et fonctionnels', async ({ page }) => {
    await page.addInitScript(() => window.localStorage.clear());
    await page.goto('/');
    await page.getByRole('button', { name: /ville/i }).first().click();
    await page.fill('#pc-city', 'Paris');
    await page.fill('#pc-country', 'France');
    await page.locator('form:has(#pc-city)').getByRole('button', { type: 'submit' }).click();
    await expect(page.getByRole('heading', { name: 'Horaires du jour' })).toBeVisible();

    await expect(page.locator('#pc-method')).toBeVisible();
    await expect(page.locator('#pc-madhhab')).toBeVisible();

    // Changer la méthode déclenche un refetch (le compteur reste lisible).
    await page.selectOption('#pc-method', '2');
    await expect(page.locator('#pc-method')).toHaveValue('2');
  });
});
