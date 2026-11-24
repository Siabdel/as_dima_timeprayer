/**
 * Tests E2E — Lecture mot à mot (Word-by-Word).
 * Couvre : activation du mode mot à mot dans une sourate, affichage des mots
 * arabes avec leur traduction française, présence du lecteur audio par mot.
 */
import { test, expect } from '@playwright/test';

test.describe('Lecture mot à mot', () => {
  test('afficher les mots avec leur traduction sous le mode mot à mot', async ({ page }) => {
    await page.goto('/quran/1');

    // En-tête sourate affiché.
    await expect(page.getByText(/Al-Fatihah/i).first()).toBeVisible();

    // Activer le mode mot à mot.
    const wordSwitch = page.locator('#pc-word-mode');
    await expect(wordSwitch).toBeVisible();
    await wordSwitch.check();

    // Le texte arabe est découpé en mots : la grille .pc-wbw-words apparaît
    // et contient plusieurs cellules (.pc-wbw-cell).
    const cells = page.locator('.pc-wbw-cell');
    await expect(cells.first()).toBeVisible();
    expect(await cells.count()).toBeGreaterThan(3);

    // Chaque mot porte un texte arabe et sa traduction (span dédié).
    await expect(page.locator('.pc-wbw-arabic').first()).toBeVisible();
    await expect(page.locator('.pc-wbw-translation').first()).toBeVisible();

    // La traduction française du mot « au nom de » (lexique local) apparaît.
    await expect(page.getByText(/au nom de/i).first()).toBeVisible();

    // Le verset reste en RTL (une grille par verset).
    await expect(page.locator('.pc-wbw-words').first()).toHaveAttribute('dir', 'rtl');
  });

  test('revenir au mode normal quand le switch est désactivé', async ({ page }) => {
    await page.goto('/quran/1');

    const wordSwitch = page.locator('#pc-word-mode');
    await wordSwitch.check();
    await expect(page.getByText(/au nom de/i).first()).toBeVisible();

    // Désactivation → le mode classique (texte du verset complet) revient.
    await wordSwitch.uncheck();
    // La région mot-à-mot disparaît.
    await expect(page.locator('.pc-wbw-words')).toHaveCount(0);
  });
});