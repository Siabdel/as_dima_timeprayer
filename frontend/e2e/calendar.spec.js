/**
 * Tests E2E — Calendrier des fêtes (islamiques + marocaines).
 * Couvre : chargement de la page, section « Prochaines fêtes », toggle de
 * filtre par type.
 */
import { test, expect } from '@playwright/test';

test.describe('Calendrier des fêtes', () => {
  test('afficher les prochaines fêtes et le calendrier annuel', async ({ page }) => {
    await page.goto('/calendar');

    // Titre de la page.
    await expect(page.getByRole('heading', { name: /calendrier/i }).first()).toBeVisible();

    // Section « Prochaines fêtes » : au moins une fête avec jours restants.
    await expect(page.getByText(/prochaines f[eê]tes/i)).toBeVisible();

    // Le calendrier annuel contient des fêtes connues (Fête du Trône en juillet).
    await expect(page.getByText(/Fête du Trône/)).toBeVisible();
  });

  test('filtrer par type (islamique / national)', async ({ page }) => {
    await page.goto('/calendar');

    // Filtre « Fêtes nationales » : bouton avec aria-pressed (toggle accessible).
    const nationalToggle = page.getByRole('button', { name: /nationales/i });
    await expect(nationalToggle).toBeVisible();
    await nationalToggle.click();
    await expect(nationalToggle).toHaveAttribute('aria-pressed', 'true');

    // Le calendrier annuel ne montre plus que les fêtes nationales.
    // (La section « Prochaines fêtes » reste informative et non filtrée.)
    const yearSection = page.locator('section[aria-labelledby="calendar-year-title"]');
    await expect(yearSection.getByText(/Fête du Trône|Marche Verte/).first()).toBeVisible();
    await expect(yearSection.getByText(/Isra & Mi'raj/)).toHaveCount(0);
  });
});
