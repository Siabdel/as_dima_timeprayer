/**
 * Tests E2E — Outils (étape 6).
 * Couvre : date hégirienne, Tasbih (compteur local), section Qibla.
 */
import { test, expect } from '@playwright/test';

test.describe('Outils', () => {
  test('afficher les trois sections (Qibla, Hégire, Tasbih)', async ({ page }) => {
    await page.goto('/tools');

    await expect(page.getByRole('heading', { name: 'Outils' })).toBeVisible();
    await expect(page.getByRole('heading', { name: /Qibla/ })).toBeVisible();
    await expect(page.getByRole('heading', { name: /Date hégirienne/ })).toBeVisible();
    await expect(page.getByRole('heading', { name: /Tasbih/ })).toBeVisible();
  });

  test('afficher la date hégirienne du jour', async ({ page }) => {
    await page.goto('/tools');

    // Format attendu : « 12 Jumada al-Akhira 1447 AH » — année 144x visible.
    await expect(page.getByText(/14[4-9][0-9]/).first()).toBeVisible();
    // Mois arabe affiché en texte arabe.
    await expect(page.locator('.arabic-text').first()).toBeVisible();
  });

  test('incrémenter le compteur Tasbih', async ({ page }) => {
    await page.goto('/tools');

    const count = page.locator('.pc-tasbih-count');
    await expect(count).toBeVisible();
    const before = await count.textContent();

    // Clic sur le grand bouton central.
    await page.locator('.pc-tasbih-button').click();
    await expect(count).toHaveText('1');
    // Correction -1 : retour à 0.
    await page.getByRole('button', { name: /retirer un/i }).click();
    await expect(count).toHaveText(before?.trim() || '0');
  });

  test('persister le compteur Tasbih dans le localStorage', async ({ page }) => {
    await page.goto('/tools');
    await page.locator('.pc-tasbih-button').click();
    await page.locator('.pc-tasbih-button').click();
    await expect(page.locator('.pc-tasbih-count')).toHaveText('2');

    // Rechargement : le compte persiste (localStorage « pc_tasbih »).
    await page.reload();
    await expect(page.locator('.pc-tasbih-count')).toHaveText('2');
  });
});
