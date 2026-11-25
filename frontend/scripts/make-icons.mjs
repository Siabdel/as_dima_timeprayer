// Génère les icônes de l'app « Salawat » (PWA) à partir d'un dessin SVG unique.
// Usage : node scripts/make-icons.mjs   (utilise Chromium de Playwright)
// Sorties dans public/icons/ : icon-192/512 (« any », coins arrondis), maskable-192/512
// (plein cadre, zone de sécurité Android), apple-touch-icon (180, plein cadre),
import { chromium } from '@playwright/test';
import { writeFileSync, mkdirSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';

const OUT = join(dirname(fileURLToPath(import.meta.url)), '..', 'public', 'icons');
mkdirSync(OUT, { recursive: true });

// Dessin (repère 512×512) : mosquée dorée — dôme, croissant, deux minarets, porte en arc.
const ART = `
  <defs>
    <linearGradient id="gold" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#FBE7A6"/><stop offset=".55" stop-color="#E9C46A"/><stop offset="1" stop-color="#C98F2E"/>
    </linearGradient>
  </defs>
  <!-- halo derrière le dôme -->
  <circle cx="256" cy="262" r="150" fill="#ffffff" opacity=".07"/>
  <!-- minarets -->
  <g fill="url(#gold)">
    <rect x="126" y="262" width="30" height="150" rx="3"/>
    <path d="M141 218 L158 262 L124 262 Z"/>
    <rect x="356" y="262" width="30" height="150" rx="3"/>
    <path d="M371 218 L388 262 L354 262 Z"/>
    <rect x="124" y="296" width="34" height="8" rx="2"/><rect x="354" y="296" width="34" height="8" rx="2"/>
    <!-- dôme central -->
    <path d="M168 346 C168 262 208 214 256 198 C304 214 344 262 344 346 Z"/>
    <!-- salle de prière -->
    <rect x="150" y="346" width="212" height="66" rx="4"/>
    <rect x="108" y="408" width="296" height="16" rx="6"/>
  </g>
  <!-- porte en arc -->
  <path d="M232 412 L232 376 C232 354 280 354 280 376 L280 412 Z" fill="#0E4F4B"/>
  <!-- croissant au sommet (vrai croissant, découpé par un masque) -->
  <mask id="cres"><rect width="512" height="512" fill="#fff"/><circle cx="272" cy="156" r="27" fill="#000"/></mask>
  <circle cx="256" cy="166" r="32" fill="url(#gold)" mask="url(#cres)"/>
  <path d="M256 190 L256 204" stroke="url(#gold)" stroke-width="6" stroke-linecap="round"/>
  <!-- étoiles -->
  <g fill="#FBE7A6" opacity=".9">
    <path d="M118 150 l5 12 12 5 -12 5 -5 12 -5 -12 -12 -5 12 -5z"/>
    <path d="M400 128 l4 9 9 4 -9 4 -4 9 -4 -9 -9 -4 9 -4z"/>
    <path d="M372 196 l3 7 7 3 -7 3 -3 7 -3 -7 -7 -3 7 -3z" opacity=".7"/>
  </g>`;

const BG = `
  <defs><linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
    <stop offset="0" stop-color="#1B8C85"/><stop offset=".55" stop-color="#14746F"/><stop offset="1" stop-color="#0B4B47"/>
  </linearGradient></defs>`;

/** SVG complet 512×512. rounded : coins arrondis (transparents) ; scale/dy : zone de sécurité. */
function svg({ rounded, scale = 1, dy = 0 }) {
  const cx = 256, cy = 262;
  return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" width="512" height="512">
  ${BG}
  <rect width="512" height="512" ${rounded ? 'rx="112"' : ''} fill="url(#bg)"/>
  <g transform="translate(${cx} ${cy + dy}) scale(${scale}) translate(${-cx} ${-cy})">${ART}</g>
</svg>`;
}

const jobs = [
  { file: 'icon-512.png', size: 512, doc: svg({ rounded: true, scale: 1.04, dy: -4 }), transparent: true },
  { file: 'icon-192.png', size: 192, doc: svg({ rounded: true, scale: 1.04, dy: -4 }), transparent: true },
  // Maskable : plein cadre, dessin réduit pour rester dans le cercle de sécurité (80 %).
  { file: 'maskable-512.png', size: 512, doc: svg({ rounded: false, scale: 0.8, dy: 6 }) },
  { file: 'maskable-192.png', size: 192, doc: svg({ rounded: false, scale: 0.8, dy: 6 }) },
  // iOS : plein cadre (iOS arrondit lui-même), dessin légèrement réduit.
  { file: 'apple-touch-icon.png', size: 180, doc: svg({ rounded: false, scale: 0.92, dy: 2 }) },
  { file: 'favicon-32.png', size: 32, doc: svg({ rounded: true, scale: 1.1, dy: -6 }), transparent: true },
  { file: 'favicon-16.png', size: 16, doc: svg({ rounded: true, scale: 1.1, dy: -6 }), transparent: true },
];

writeFileSync(join(OUT, 'favicon.svg'), svg({ rounded: true, scale: 1.04, dy: -4 }));

const browser = await chromium.launch();
const page = await browser.newPage();
for (const j of jobs) {
  await page.setViewportSize({ width: j.size, height: j.size });
  await page.setContent(
    `<html><body style="margin:0;background:transparent"><div style="width:${j.size}px;height:${j.size}px">` +
      j.doc.replace('width="512" height="512"', `width="${j.size}" height="${j.size}"`) +
      '</div></body></html>'
  );
  await page.screenshot({ path: join(OUT, j.file), omitBackground: !!j.transparent, clip: { x: 0, y: 0, width: j.size, height: j.size } });
  console.log('ok', j.file);
}
await browser.close();
