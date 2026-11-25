/**
 * Changement de récitateur pendant l'écoute :
 *  - sourate absente chez le nouveau récitateur (404) → message clair + retour au précédent ;
 *  - pas d'audio verset par verset → repli sur la sourate entière + information.
 */
import { test, expect } from '@playwright/test';

const json = (route, status, body) =>
  route.fulfill({ status, contentType: 'application/json', body: JSON.stringify(body) });

test.describe('Changement de récitateur', () => {
  test.beforeEach(async ({ page }) => {
    await page.addInitScript(() => window.localStorage.clear());
  });

  test('sourate indisponible : message clair et récitateur précédent conservé', async ({ page }) => {
    await page.route('**/quran/audio/chapter/1/?reciter_id=benmoussa', (route) =>
      json(route, 404, { error: { code: 'not_available', message: "Cette sourate n'est pas disponible pour ce récitateur." } })
    );
    await page.goto('/quran/1');
    await page.getByRole('button', { name: /Écouter la sourate/ }).click();
    const select = page.locator('select').last();
    await expect(select).toBeVisible();
    const before = await select.inputValue();

    await select.selectOption('benmoussa');
    await expect(page.getByText("pas disponible pour ce récitateur")).toBeVisible();
    await expect(select).toHaveValue(before); // retour au récitateur précédent
  });

  test('limite de requêtes : message explicite', async ({ page }) => {
    await page.route('**/quran/audio/chapter/1/?reciter_id=benmoussa', (route) =>
      json(route, 429, { detail: 'throttled' })
    );
    await page.goto('/quran/1');
    await page.getByRole('button', { name: /Écouter la sourate/ }).click();
    const select = page.locator('select').last();
    await select.selectOption('benmoussa');
    await expect(page.getByText(/Trop de requêtes/)).toBeVisible();
  });

  test('pas d\'audio verset : repli sur la sourate entière', async ({ page }) => {
    await page.route('**/quran/audio/verse/?*reciter_id=benmoussa*', (route) =>
      json(route, 400, { error: { code: 'invalid_params', message: 'reciter_id doit être un entier.' } })
    );
    await page.goto('/quran/1');
    await page.getByRole('button', { name: /Lire le verset 1/ }).click();
    const select = page.locator('select').last();
    await expect(select).toBeVisible();

    await select.selectOption('benmoussa');
    await expect(page.getByText(/ne propose pas la lecture verset par verset/)).toBeVisible();
    await expect(select).toHaveValue('benmoussa');
  });
});
