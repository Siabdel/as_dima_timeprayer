/**
 * Tests E2E — Récitateur hébergé localement : Cheikh Abderrahmane Benmoussa.
 * Vérifie que le récitateur est proposé dans le sélecteur, que son MP3 est
 * servi par l'application et que l'API renvoie la bonne URL.
 */
import { test, expect } from '@playwright/test';

const API_BASE = process.env.E2E_API_BASE_URL || 'http://localhost:8000/api/v1';

test.describe('Récitateur Benmoussa (local)', () => {
  test('proposer Benmoussa dans la liste des récitateurs', async ({ request }) => {
    const resp = await request.get(`${API_BASE}/quran/reciters/`);
    expect(resp.ok()).toBeTruthy();
    const data = await resp.json();
    const benmoussa = (data.chapter || []).find((r) => r.id === 'benmoussa');
    expect(benmoussa).toBeTruthy();
    expect(benmoussa.name).toContain('Benmoussa');
  });

  test("servir l'URL audio du chapitre 1 pour Benmoussa", async ({ request }) => {
    const resp = await request.get(`${API_BASE}/quran/audio/chapter/1/`, {
      params: { reciter_id: 'benmoussa' },
    });
    expect(resp.ok()).toBeTruthy();
    const { audio_url } = await resp.json();
    expect(audio_url).toBe('/quran/benmoussa/001.mp3');
  });

  test('servir le fichier MP3 depuis le frontend', async ({ request }) => {
    // Requête vers le serveur Vite : le fichier doit être accessible.
    const resp = await request.get('/quran/benmoussa/001.mp3');
    expect(resp.status()).toBe(200);
    expect(resp.headers()['content-type']).toContain('audio');
  });

  test('refuser un récitateur texte inconnu', async ({ request }) => {
    const resp = await request.get(`${API_BASE}/quran/audio/chapter/1/`, {
      params: { reciter_id: 'recitateur-inexistant' },
    });
    expect(resp.status()).toBe(400);
  });
});