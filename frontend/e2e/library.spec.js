/**
 * Tests E2E — Cahier de douâas et hadiths.
 * Couvre : chargement des deux onglets, filtre par catégorie, affichage du
 * texte arabe RTL + source citée.
 */
import { test, expect } from '@playwright/test';

test.describe('Cahier Douâa & Hadiths', () => {
  test('afficher les douâas avec texte arabe et source', async ({ page }) => {
    await page.goto('/library');

    // Onglet « Douâas » actif par défaut : une douâa connue est visible.
    await expect(page.getByText(/dou[aâ]as/i).first()).toBeVisible();
    await expect(page.getByText(/Douâa au réveil|Douâa avant de manger/).first()).toBeVisible();

    // Le texte arabe est rendu en RTL.
    const arabic = page.locator('[dir="rtl"]').first();
    await expect(arabic).toBeVisible();
    await expect(arabic).toHaveCSS('direction', 'rtl');

    // Une source de recueil canonique est affichée.
    await expect(page.getByText(/Sahîh al-Bukhârî|Sahîh Muslim|Abû Dâwûd|Tirmidhî/).first()).toBeVisible();
  });

  test("basculer vers l'onglet Hadiths", async ({ page }) => {
    await page.goto('/library');

    // Les onglets sont des role="tab" (nav-pills Bootstrap), pas des liens.
    await page.getByRole('tab', { name: /hadiths/i }).click();

    // Un hadith connu : « Les actes valent par les intentions ».
    await expect(page.getByText(/Les actes valent par les intentions/)).toBeVisible();
    // Narrateur affiché.
    await expect(page.getByText(/Umar ibn al-Khatt/i)).toBeVisible();
  });

  test('filtrer les douâas par catégorie', async ({ page }) => {
    await page.goto('/library');

    // Catégorie « Repas » → la douâa du jeûneur apparaît.
    await page.getByRole('button', { name: /repas/i }).click();
    await expect(page.getByText(/jeûneur à la rupture|Douâa avant de manger/).first()).toBeVisible();
  });
});
