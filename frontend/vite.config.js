// Configuration Vite 5 du frontend « Prière & Coran ».
// - Vue 3 via @vitejs/plugin-vue
// - PWA via vite-plugin-pwa (autoUpdate) avec manifest conforme à l'identité
//   visuelle et service worker personnalisé (src/sw.js, stratégie
//   injectManifest) : notifications Web Push + lecture du son d'Adhan.
// - IMPORTANT : aucune mise en cache runtime des réponses API (données
//   potentiellement authentifiées). Seule la coquille applicative
//   (JS/CSS/HTML/images/polices) est pré-cachée par Workbox.
import { defineConfig } from 'vite';
import vue from '@vitejs/plugin-vue';
import { VitePWA } from 'vite-plugin-pwa';

export default defineConfig({
  plugins: [
    vue(),
    VitePWA({
      registerType: 'autoUpdate',
      includeAssets: [
        'icons/favicon.svg', 'icons/favicon-32.png', 'icons/favicon-16.png',
        'icons/apple-touch-icon.png', 'icons/icon-192.png', 'icons/icon-512.png',
        'icons/maskable-192.png', 'icons/maskable-512.png'
      ],
      // Stratégie « injectManifest » : le service worker est écrit à la main
      // (src/sw.js) pour gérer les notifications Web Push (affichage +
      // transmission du son d'Adhan à une fenêtre ouverte). vite-plugin-pwa
      // y injecte la liste de pré-cache (self.__WB_MANIFEST) et bundle les
      // imports Workbox.
      strategies: 'injectManifest',
      srcDir: 'src',
      filename: 'sw.js',
      injectManifest: {
        // Pré-cache limité aux ressources statiques de la coquille
        // applicative. Les MP3 d'Adhan (public/adhan/*.mp3, ~5 MB chacun)
        // sont volontairement EXCLUS : lecture en ligne au moment du push.
        globPatterns: ['**/*.{js,css,html,svg,png,woff,woff2,ico}'],
      },
      manifest: {
        name: 'Salawat — Prière & Coran',
        short_name: 'Salawat',
        description: 'Horaires de prière, météo, rappels Adhan et lecture du Saint Coran',
        theme_color: '#14746F',
        background_color: '#f8f9fa',
        display: 'standalone',
        id: '/',
        start_url: '/',
        scope: '/',
        lang: 'fr',
        categories: ['lifestyle', 'books', 'education'],
        // Raccourcis (appui long sur l'icône de l'app installée)
        shortcuts: [
          { name: 'Horaires de prière', url: '/', icons: [{ src: '/icons/icon-192.png', sizes: '192x192' }] },
          { name: 'Coran', url: '/quran', icons: [{ src: '/icons/icon-192.png', sizes: '192x192' }] },
          { name: 'Réglages', url: '/settings', icons: [{ src: '/icons/icon-192.png', sizes: '192x192' }] }
        ],
        icons: [
          { src: '/icons/icon-192.png', sizes: '192x192', type: 'image/png', purpose: 'any' },
          { src: '/icons/icon-512.png', sizes: '512x512', type: 'image/png', purpose: 'any' },
          { src: '/icons/maskable-192.png', sizes: '192x192', type: 'image/png', purpose: 'maskable' },
          { src: '/icons/maskable-512.png', sizes: '512x512', type: 'image/png', purpose: 'maskable' }
        ]
      }
    })
  ],
  server: {
    host: '0.0.0.0',
    port: 5173
  }
});
