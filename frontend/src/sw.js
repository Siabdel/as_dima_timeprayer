// ===========================================================================
// Service worker personnalisé (vite-plugin-pwa, stratégie « injectManifest »).
// ---------------------------------------------------------------------------
// Reprend le pré-cache Workbox de la coquille applicative (comme la version
// générée par défaut) et AJOUTE la gestion des notifications Web Push :
//   * « push »           : affiche la notification Adhan puis transmet
//                          { type: 'PLAY_ADHAN', soundUrl } à une fenêtre
//                          ouverte de l'app — un service worker ne peut pas
//                          jouer d'audio lui-même ;
//   * « notificationclick» : met l'app au premier plan (ou l'ouvre).
//
// IMPORTANT : les MP3 d'Adhan ne sont PAS pré-cachés (5 MB chacun) — la
// lecture est faite par une fenêtre de l'app, au moment du push, en ligne.
// ===========================================================================
import { clientsClaim } from 'workbox-core';
import {
  cleanupOutdatedCaches,
  createHandlerBoundToURL,
  precacheAndRoute,
} from 'workbox-precaching';
import { NavigationRoute, registerRoute } from 'workbox-routing';
import { CacheFirst } from 'workbox-strategies';
import { RangeRequestsPlugin } from 'workbox-range-requests';
import { ExpirationPlugin } from 'workbox-expiration';
import { CacheableResponsePlugin } from 'workbox-cacheable-response';

// --- Pré-cache de la coquille applicative (généré par vite-plugin-pwa) -----
precacheAndRoute(self.__WB_MANIFEST);
cleanupOutdatedCaches();

// Application monopage : toute navigation bascule sur index.html pré-caché.
registerRoute(new NavigationRoute(createHandlerBoundToURL('/index.html')));

// Audio du Coran : cache d'exécution (écoute hors ligne + économie de données).
// Les requêtes « Range » (lecture/seek) sont servies depuis le cache ; la page
// Réglages permet de le vider (cache « pc-audio-v1 »).
registerRoute(
  ({ request }) => request.destination === 'audio',
  new CacheFirst({
    cacheName: 'pc-audio-v1',
    plugins: [
      new CacheableResponsePlugin({ statuses: [200] }),
      new RangeRequestsPlugin(),
      new ExpirationPlugin({ maxEntries: 40, purgeOnQuotaError: true }),
    ],
  })
);

// Prend le contrôle de toutes les fenêtres dès l'activation (autoUpdate).
clientsClaim();

// ---------------------------------------------------------------------------
// Événement « push » : affiche la notification et orchestre la lecture du son
// ---------------------------------------------------------------------------
self.addEventListener('push', (event) => {
  let payload = {};
  try {
    payload = event.data ? event.data.json() : {};
  } catch {
    // Payload non JSON : notification générique pour rester visible.
    payload = { title: '🕌 Adhan', body: "Il est l'heure de la prière." };
  }

  const soundUrl = payload.data?.sound_url ?? null;
  const alertMode = payload.data?.alert_mode ?? 'full';
  const options = {
    // Vibreur : motif long pour « vibrate », court sinon ; rien si bip/son seuls.
    vibrate: alertMode === 'vibrate' ? [400, 150, 400, 150, 400] : undefined,
    body: payload.body || '',
    tag: payload.tag || 'prayer',
    icon: '/icons/icon-192.png',
    badge: '/icons/icon-192.png',
    data: payload.data || {},
  };

  event.waitUntil(
    (async () => {
      await self.registration.showNotification(payload.title || '🕌 Adhan', options);

      // Lecture du son : une fenêtre ouverte de l'app est nécessaire.
      if (!soundUrl && alertMode !== 'beep') return;
      const windows = await self.clients.matchAll({
        type: 'window',
        includeUncontrolled: true,
      });
      for (const win of windows) {
        win.postMessage({
          type: 'PLAY_ADHAN',
          soundUrl,
          alertMode,
          volume: payload.data?.volume ?? 100,
          fadeIn: payload.data?.fade_in === true,
        });
        break; // une seule fenêtre joue le son
      }
    })()
  );
});

// ---------------------------------------------------------------------------
// Événement « notificationclick » : ouvre / met au premier plan l'app
// ---------------------------------------------------------------------------
self.addEventListener('notificationclick', (event) => {
  event.notification.close();
  const target = new URL('/', self.location.origin).href;

  event.waitUntil(
    (async () => {
      const windows = await self.clients.matchAll({
        type: 'window',
        includeUncontrolled: true,
      });
      for (const win of windows) {
        if (win.url === target && 'focus' in win) {
          await win.focus();
          return;
        }
      }
      if (self.clients.openWindow) {
        await self.clients.openWindow(target);
      }
    })()
  );
});
