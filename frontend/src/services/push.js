// ===========================================================================
// Service Web Push (côté navigateur) — encapsule TOUTE la logique :
// permission Notification, service worker, PushManager, synchronisation
// avec le backend (/notifications/subscribe/).
// ---------------------------------------------------------------------------
// Prérequis PWA : le service worker « /sw.js » est généré par vite-plugin-pwa
// (registerType « autoUpdate », injection automatique de l'appel registerSW
// dans index.html). Ce service ne fait QUE consommer cette registration.
//
// Toutes les erreurs sont levées sous forme de PushError (code stable +
// message français prêt à afficher) afin que la vue n'ait qu'à les relayer.
// ===========================================================================
import {
  getVapidKey,
  subscribePush,
  unsubscribePush,
  sendTestNotification,
} from '../api/tools';

/**
 * Erreur métier Web Push : `code` stable (machine) et `message` en français
 * (humain, affichable tel quel dans l'interface).
 */
export class PushError extends Error {
  /**
   * @param {string} code « unsupported » | « permission_denied » |
   *        « vapid_key_unavailable » | « subscribe_failed » | « server_error »
   * @param {string} message message français prêt à afficher
   */
  constructor(code, message) {
    super(message);
    this.name = 'PushError';
    this.code = code;
  }
}

/**
 * Vrai si le navigateur gère les notifications push (service worker +
 * PushManager + API Notification).
 * @returns {boolean}
 */
export function isPushSupported() {
  return (
    typeof window !== 'undefined' &&
    'serviceWorker' in navigator &&
    'PushManager' in window &&
    'Notification' in window
  );
}

/**
 * Convertit une clé VAPID base64url (sans remplissage) en Uint8Array,
 * format attendu par pushManager.subscribe({ applicationServerKey }).
 * @param {string} base64String clé publique VAPID base64url
 * @returns {Uint8Array}
 */
export function urlBase64ToUint8Array(base64String) {
  const padding = '='.repeat((4 - (base64String.length % 4)) % 4);
  const base64 = (base64String + padding).replace(/-/g, '+').replace(/_/g, '/');
  const raw = window.atob(base64);
  const output = new Uint8Array(raw.length);
  for (let i = 0; i < raw.length; i += 1) {
    output[i] = raw.charCodeAt(i);
  }
  return output;
}

/**
 * Retourne la registration du service worker de l'application :
 * - celle créée par l'auto-enregistrement de vite-plugin-pwa si elle existe ;
 * - sinon, enregistre explicitement « /sw.js » puis attend qu'elle soit prête.
 * @returns {Promise<ServiceWorkerRegistration>}
 */
async function getServiceWorkerRegistration() {
  const existing = await navigator.serviceWorker.getRegistration();
  if (existing) return existing;
  // Repli : enregistrement explicite (même fichier que celui du plugin).
  await navigator.serviceWorker.register('/sw.js');
  return navigator.serviceWorker.ready;
}

/**
 * Demande la permission de notifier, récupère la clé VAPID du backend,
 * crée l'abonnement push dans le navigateur puis l'enregistre côté serveur.
 * @returns {Promise<PushSubscription>} l'abonnement navigateur créé
 * @throws {PushError} avec un message français actionnable
 */
export async function requestPermissionAndSubscribe() {
  if (!isPushSupported()) {
    throw new PushError(
      'unsupported',
      "Les notifications push ne sont pas prises en charge par ce navigateur."
    );
  }

  // 1) Permission : on ne demande QUE si l'état est encore indécis (« default »).
  let permission = Notification.permission;
  if (permission === 'default') {
    try {
      permission = await Notification.requestPermission();
    } catch {
      permission = 'denied';
    }
  }
  if (permission !== 'granted') {
    throw new PushError(
      'permission_denied',
      "Permission refusée : autorisez les notifications dans les réglages de votre navigateur pour recevoir les rappels de prière."
    );
  }

  // 2) Clé publique VAPID fournie par le backend (endpoint public).
  let vapidKey = null;
  try {
    const response = await getVapidKey();
    vapidKey = response.data?.public_key ?? null;
  } catch {
    vapidKey = null;
  }
  if (!vapidKey) {
    throw new PushError(
      'vapid_key_unavailable',
      "Impossible de récupérer la clé d'abonnement (VAPID). Vérifiez votre connexion et réessayez."
    );
  }

  // 3) Abonnement navigateur (chiffrement p256dh + auth générés ici).
  const registration = await getServiceWorkerRegistration();
  let subscription;
  try {
    subscription = await registration.pushManager.subscribe({
      userVisibleOnly: true,
      applicationServerKey: urlBase64ToUint8Array(vapidKey),
    });
  } catch {
    throw new PushError(
      'subscribe_failed',
      "L'abonnement du navigateur a échoué. Vérifiez que les notifications sont autorisées pour ce site, puis réessayez."
    );
  }

  // 4) Sérialisation et enregistrement côté backend (JWT requis).
  const json = subscription.toJSON();
  if (!json.endpoint || !json.keys?.p256dh || !json.keys?.auth) {
    // Abonnement incomplet (rare) : on le révoque pour ne pas laisser un
    // abonnement inutilisable côté navigateur.
    try {
      await subscription.unsubscribe();
    } catch {
      /* ignore */
    }
    throw new PushError(
      'subscribe_failed',
      "L'abonnement du navigateur est incomplet (clés de chiffrement indisponibles). Réessayez ou utilisez un autre navigateur."
    );
  }

  try {
    await subscribePush({
      endpoint: json.endpoint,
      keys: { p256dh: json.keys.p256dh, auth: json.keys.auth },
      user_agent: typeof navigator !== 'undefined' ? navigator.userAgent : '',
    });
  } catch {
    // Le navigateur est abonné mais le serveur n'a pas pu enregistrer :
    // on révoque l'abonnement local pour rester dans un état cohérent.
    try {
      await subscription.unsubscribe();
    } catch {
      /* ignore */
    }
    throw new PushError(
      'server_error',
      "L'enregistrement de l'abonnement a échoué côté serveur. Connectez-vous puis réessayez."
    );
  }

  return subscription;
}

/**
 * Abonnement push existant DANS CE NAVIGATEUR (null si aucun ou non supporté).
 * Ne contacte jamais le backend.
 * @returns {Promise<PushSubscription | null>}
 */
export async function getExistingSubscription() {
  if (!isPushSupported()) return null;
  try {
    const registration = await navigator.serviceWorker.getRegistration();
    if (!registration) return null;
    return (await registration.pushManager.getSubscription()) ?? null;
  } catch {
    // Service worker indisponible (mode privé, permissions…) : pas d'abonnement.
    return null;
  }
}

/**
 * Désabonnement complet : backend d'abord (DELETE /notifications/subscribe/),
 * puis révocation de l'abonnement dans le navigateur. Idempotent : renvoie un
 * résultat explicite même s'il n'y avait aucun abonnement.
 * @returns {Promise<{ browserUnsubscribed: boolean, serverUnsubscribed: boolean,
 *           error: Error | null }>}
 */
export async function unsubscribe() {
  const subscription = await getExistingSubscription();
  if (!subscription) {
    return { browserUnsubscribed: false, serverUnsubscribed: false, error: null };
  }

  let serverUnsubscribed = true;
  let error = null;
  try {
    await unsubscribePush(subscription.endpoint);
  } catch (err) {
    // On poursuit malgré tout : le navigateur ne doit PAS rester abonné.
    serverUnsubscribed = false;
    error = err;
  }

  let browserUnsubscribed = true;
  try {
    await subscription.unsubscribe();
  } catch {
    browserUnsubscribed = false;
  }

  return { browserUnsubscribed, serverUnsubscribed, error };
}

/**
 * Envoie une notification de test pour la prière donnée (throttle serveur :
 * 5 envois/heure → 429 possible ; 400 « no_subscription » si jamais abonné).
 * @param {string} prayerName « fajr|sunrise|dhuhr|asr|maghrib|isha »
 * @returns {Promise<Object>} { status: 'sent', sent, removed }
 */
export function sendTest(prayerName) {
  return sendTestNotification(prayerName);
}
