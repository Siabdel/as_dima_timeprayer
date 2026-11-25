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

test.describe('Calendrier : onglet France', () => {
  test('deux onglets, jours fériés français avec fêtes mobiles', async ({ page }) => {
    await page.goto('/calendar');
    await expect(page.getByRole('tab', { name: 'Calendrier islamique et fêtes marocaines' })).toHaveAttribute('aria-selected', 'true');

    await page.getByRole('tab', { name: 'Calendrier grégorien, France' }).click();
    await expect(page.getByRole('heading', { name: /Jours fériés \d{4} — France/ })).toBeVisible();
    for (const name of ['Lundi de Pâques', 'Ascension', 'Lundi de Pentecôte', 'Fête nationale']) {
      await expect(page.getByText(name, { exact: true }).first()).toBeVisible();
    }

    // Retour au premier onglet.
    await page.getByRole('tab', { name: /islamique/ }).click();
    await expect(page.getByText(/prochaines f[eê]tes/i)).toBeVisible();
  });

  test('onglet Spécial Ramadan : horaires, imsak, rupture et Nuit du Destin', async ({ page }) => {
    await page.addInitScript(() => {
      window.localStorage.setItem('pc_prayer_location', JSON.stringify({
        location: { latitude: 48.85, longitude: 2.35 }, method: 12, madhhab: 'standard' }));
    });
    const days = Array.from({ length: 29 }, (_, i) => ({
      date: new Date(Date.UTC(2027, 1, 8 + i)).toISOString().slice(0, 10), hijri_day: i + 1,
      imsak: '06:10', fajr: '06:20', sunrise: '07:40', dhuhr: '13:00', asr: '15:30', maghrib: '18:00', isha: '19:10' }));
    await page.route('**/prayer-times/ramadan/**', (route) => route.fulfill({ json: {
      hijri_year: 1448, location: {}, method: 12, madhhab: 'standard', timezone: 'Europe/Paris',
      start_date: days[0].date, end_date: days[28].date, days_count: 29, days, stale: false,
      key_dates: [{ id: 'laylat-al-qadr', name: 'Nuit du Destin (Laylat al-Qadr)', name_ar: 'ليلة القدر',
        date: days[25].date, hijri_day: 27, night: true, description: 'Nuit la plus attendue.', highlight: true }] } }));
    await page.goto('/calendar');
    await page.getByRole('tab', { name: 'Spécial Ramadan' }).click();
    await expect(page.getByRole('heading', { name: /Ramadan 1448/ })).toBeVisible();
    await expect(page.getByText('Nuit du Destin (Laylat al-Qadr)')).toBeVisible();
    await expect(page.getByRole('columnheader', { name: 'Rupture' })).toBeVisible();
    await expect(page.locator('tbody tr')).toHaveCount(29);
  });

  test('menu principal : entrée Ramadan vers /ramadan', async ({ page }) => {
    await page.goto('/');
    await page.getByRole('link', { name: 'Ramadan', exact: true }).click();
    await expect(page).toHaveURL(/\/ramadan$/);
    await expect(page.getByRole('heading', { name: /Ramadan/ }).first()).toBeVisible();
  });
});
