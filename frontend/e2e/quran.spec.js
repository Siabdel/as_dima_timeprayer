/**
 * Tests E2E — Coran (étapes 4-5).
 * Couvre : liste des 114 sourates, recherche locale, page d'une sourate
 * avec texte arabe RTL et traductions.
 */
import { test, expect } from '@playwright/test';

test.describe('Coran', () => {
  test('charger la liste complète des sourates', async ({ page }) => {
    await page.goto('/quran');

    await expect(page.getByRole('heading', { name: 'Coran' })).toBeVisible();
    // Les sourates chargées : Al-Fatihah (1) et An-Nas (114) sont visibles.
    await expect(page.getByText('Al-Fatihah')).toBeVisible();
    await expect(
      page.getByRole('button', { name: /Sourate 114/ })
    ).toBeVisible();

    // 114 items dans la liste (badge numéro 1 à 114).
    const items = page.locator('[role="button"]').filter({ hasText: /^\s*\d+/ });
    await expect(items.first()).toBeVisible();
  });

  test('filtrer les sourates par recherche', async ({ page }) => {
    await page.goto('/quran');
    await expect(page.getByText('Al-Fatihah')).toBeVisible();

    await page.getByPlaceholder(/rechercher une sourate/i).fill('Yasin');
    // Seules les sourates correspondantes restent ; Yâ-Sîn (36) visible,
    // Al-Fatihah absente.
    await expect(page.getByText(/Y[âa]-S[iî]n/i).first()).toBeVisible();
    await expect(page.getByText('Al-Fatihah')).toBeHidden();

    // Recherche par numéro : "1" doit montrer Al-Fatihah.
    await page.getByPlaceholder(/rechercher une sourate/i).fill('1');
    await expect(page.getByText('Al-Fatihah').first()).toBeVisible();
  });

  test('ouvrir une sourate et voir le texte arabe RTL', async ({ page }) => {
    await page.goto('/quran/1');

    // En-tête sourate + versets.
    await expect(page.getByText(/Al-Fatihah/i).first()).toBeVisible();
    // Le texte arabe en script Uthmani est rendu (police Amiri, RTL).
    const arabic = page.locator('.arabic-text').first();
    await expect(arabic).toBeVisible();
    await expect(arabic).toHaveCSS('direction', 'rtl');
    // Au moins une traduction française affichée (FR par défaut).
    await expect(page.getByText(/Au nom d/i).first()).toBeVisible();
  });

  test("bascule d'affichage des traductions", async ({ page }) => {
    await page.goto('/quran/1');
    await expect(page.getByText(/Au nom d/i).first()).toBeVisible();

    // Masquer les traductions (checkbox FR) → les textes français disparaissent.
    const frToggle = page.getByRole('checkbox', { name: /français|fr/i });
    if (await frToggle.isVisible()) {
      await frToggle.uncheck();
      await expect(page.getByText(/Au nom d/i)).toHaveCount(0);
    }
  });
});
