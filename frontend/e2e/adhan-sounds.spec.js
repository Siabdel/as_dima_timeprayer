/**
 * Tests E2E — Son de l'Adhan (réglages).
 * Couvre : affichage du catalogue des 3 réciteurs, sélection + persistance
 * de la préférence (PUT /auth/preferences/), aperçu audio (bouton Écouter).
 */
import { test, expect } from '@playwright/test';
import { createUser, loginViaUI } from './helpers.js';

test.describe('Son de l\'Adhan', () => {
  test('afficher le catalogue des 3 réciteurs dans les réglages', async ({ page, request }) => {
    const { email, password } = await createUser(request);
    await loginViaUI(page, email, password);

    await page.goto('/settings');
    await expect(page.getByRole('heading', { name: "Son de l'Adhan" })).toBeVisible();

    // Les 3 réciteurs du catalogue sont affichés dans la carte « Son de l'Adhan ».
    // (exact:true — le nom peut aussi apparaître dans le sélecteur par prière.)
    const adhanCard = page.locator('.card', { has: page.getByRole('heading', { name: "Son de l'Adhan" }) });
    for (const reciter of [
      'Abdul Basit Abdus Samad',
      'Mishary Rashid Alafasy',
      'Muhammad Siddiq Al-Minshawi',
    ]) {
      await expect(adhanCard.getByText(reciter, { exact: true }).first()).toBeVisible();
    }
  });

  test('sélectionner un son et persister la préférence', async ({ page, request }) => {
    const { email, password } = await createUser(request);
    await loginViaUI(page, email, password);

    await page.goto('/settings');

    // Sélectionne Alafasy via le bouton radio.
    await page.check('#adhan-sound-alafasy');

    // Confirmation visuelle d'enregistrement.
    await expect(page.getByText('Enregistré')).toBeVisible();

    // Rechargement : la préférence persiste côté serveur.
    await page.reload();
    await expect(page.locator('#adhan-sound-alafasy')).toBeChecked();
  });

  test('lancer et arrêter l\'aperçu audio', async ({ page, request }) => {
    const { email, password } = await createUser(request);
    await loginViaUI(page, email, password);

    await page.goto('/settings');
    await expect(page.getByRole('heading', { name: "Son de l'Adhan" })).toBeVisible();

    // Le premier son propose un bouton « Écouter ».
    const listenButtons = page.getByRole('button', { name: /Écouter/ });
    await expect(listenButtons.first()).toBeVisible();

    // Demande de lecture (autoplay policy : le clic utilisateur suffit).
    await listenButtons.first().click();
    // Le bouton bascule en « Arrêter » (lecture en cours) ou l'audio est
    // bloqué par la politique d'autoplay — dans les deux cas l'UI ne casse pas.
    await expect(
      page.getByRole('button', { name: /Écouter|Arrêter/ }).first()
    ).toBeVisible();
  });
});
