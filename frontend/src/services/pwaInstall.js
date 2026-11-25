// ===========================================================================
// Installation de la PWA : état partagé (bannière + Réglages).
// - Android / ordinateur : le navigateur émet « beforeinstallprompt » ; on le
//   garde pour déclencher la boîte d'installation au clic de l'utilisateur ;
// - iPhone / iPad (Safari) : aucun événement n'existe, on affiche les étapes
//   « Partager → Sur l'écran d'accueil » ;
// - Déjà installée (mode standalone) : rien n'est proposé.
// ===========================================================================
import { reactive } from 'vue';

const DISMISS_KEY = 'pc_install_dismissed_at';
const DISMISS_DAYS = 7;

let deferredPrompt = null;

export const installState = reactive({
  /** Le navigateur propose l'installation native (Android / Chrome / Edge). */
  canPrompt: false,
  /** iPhone / iPad : installation manuelle via le menu Partager de Safari. */
  isIos: false,
  /** L'app tourne déjà installée. */
  isStandalone: false,
  /** Bannière masquée par l'utilisateur (pendant 7 jours). */
  dismissed: false,
});

function detect() {
  const ua = navigator.userAgent || '';
  const ios =
    /iphone|ipad|ipod/i.test(ua) ||
    // iPadOS se présente comme un Mac tactile
    (navigator.platform === 'MacIntel' && navigator.maxTouchPoints > 1);
  installState.isIos = ios;
  installState.isStandalone =
    window.matchMedia?.('(display-mode: standalone)')?.matches === true ||
    navigator.standalone === true;
  try {
    const at = Number(window.localStorage.getItem(DISMISS_KEY) || 0);
    installState.dismissed = at > 0 && Date.now() - at < DISMISS_DAYS * 86400000;
  } catch {
    installState.dismissed = false;
  }
}

/** À appeler une fois au démarrage de l'app. */
export function initPwaInstall() {
  if (typeof window === 'undefined') return;
  detect();
  window.addEventListener('beforeinstallprompt', (event) => {
    event.preventDefault(); // on affiche notre propre invitation
    deferredPrompt = event;
    installState.canPrompt = true;
  });
  window.addEventListener('appinstalled', () => {
    deferredPrompt = null;
    installState.canPrompt = false;
    installState.isStandalone = true;
  });
}

/** Déclenche la boîte d'installation native. @returns {Promise<'accepted'|'dismissed'|'unavailable'>} */
export async function promptInstall() {
  if (!deferredPrompt) return 'unavailable';
  const event = deferredPrompt;
  deferredPrompt = null;
  installState.canPrompt = false;
  await event.prompt();
  const choice = await event.userChoice.catch(() => ({ outcome: 'dismissed' }));
  return choice.outcome === 'accepted' ? 'accepted' : 'dismissed';
}

/** Masque l'invitation pendant 7 jours. */
export function dismissInstall() {
  installState.dismissed = true;
  try {
    window.localStorage.setItem(DISMISS_KEY, String(Date.now()));
  } catch {
    /* stockage indisponible : masquée pour la session */
  }
}

/** Faut-il proposer l'installation (Android natif ou étapes iOS) ? */
export function installAvailable() {
  return !installState.isStandalone && (installState.canPrompt || installState.isIos);
}
