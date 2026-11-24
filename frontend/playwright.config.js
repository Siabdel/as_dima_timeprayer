/**
 * Configuration Playwright pour les tests E2E du frontend « Prière & Coran ».
 *
 * Usage :
 *   npx playwright test                      → tous les tests
 *   npx playwright test --ui                 → mode interactif
 *   npx playwright test e2e/auth.spec.js     → un seul fichier
 *
 * Prérequis : la stack de développement doit être lancée
 *   docker compose up -d
 *   → frontend sur http://localhost:5173, API sur http://localhost:8000
 */
import { defineConfig, devices } from '@playwright/test';

// L'application sous test : le serveur Vite de développement.
const BASE_URL = process.env.E2E_BASE_URL || 'http://localhost:5173';

export default defineConfig({
  testDir: './e2e',
  // Fichiers de tests globaux : auth.spec, prayer-times.spec, quran.spec, tools.spec
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined, // 1 worker en CI pour éviter les conflits de compte
  reporter: process.env.CI ? 'github' : [['list'], ['html', { open: 'never' }]],
  // Purge des compteurs de throttle Redis avant la suite (voir global-setup.js).
  globalSetup: './e2e/global-setup.js',

  use: {
    baseURL: BASE_URL,
    trace: 'on-first-retry', // capture de traces pour déboguer les échecs
    screenshot: 'only-on-failure',
    locale: 'fr-FR',
    // Le dev server Vite compile les modules à la première visite : timeouts
    // généreux pour éviter les faux positifs au premier passage.
    navigationTimeout: 30_000,
    actionTimeout: 15_000,
  },

  expect: {
    timeout: 10_000,
  },

  // Navigateurs testés : Chromium suffit pour le MVP ;
  // décommentez firefox/webkit pour élargir la couverture.
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
    // {
    //   name: 'firefox',
    //   use: { ...devices['Desktop Firefox'] },
    // },
    // {
    //   name: 'webkit',
    //   use: { ...devices['Desktop Safari'] },
    // },
  ],

  // Les services (frontend + backend) doivent déjà tourner :
  // on ne les gère PAS ici (docker compose up avant les tests).
  webServer: undefined,
});
