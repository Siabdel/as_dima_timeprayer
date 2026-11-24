// ===========================================================================
// Lecture du son d'Adhan (côté fenêtre de l'application).
// ---------------------------------------------------------------------------
// Deux usages :
//   1. Aperçu dans les réglages (bouton « Écouter ») ;
//   2. Lecture déclenchée par une notification push : le service worker
//      reçoit l'événement « push », affiche la notification puis transmet
//      { type: 'PLAY_ADHAN', soundUrl } à une fenêtre ouverte de l'app
//      (un SW ne peut PAS jouer d'audio lui-même). Ce module écoute ces
//      messages et joue le son.
//
// L'URL du son est relative (ex. « /adhan/abdul-basit.mp3 ») : résolue par
// rapport à l'origine de l'app, le MP3 est donc servi par le frontend.
// ===========================================================================

/** Élément <audio> courant (une seule lecture à la fois, app-wide). */
let currentAudio = null;

/** Callback optionnel notifiant l'UI du changement d'état (lecture/arrêt). */
let onStateChange = null;

/**
 * Enregistre un écouteur d'état (appelé avec `true` quand une lecture
 * démarre, `false` quand elle s'arrête). Utilisé par le sélecteur des
 * réglages pour afficher l'état « en lecture ».
 * @param {(playing: boolean) => void} callback
 */
export function setAdhanAudioStateListener(callback) {
  onStateChange = callback;
}

/** Notifie l'UI du changement d'état (silencieux si aucun écouteur). */
function notifyStateChange(playing) {
  if (typeof onStateChange === 'function') {
    try {
      onStateChange(playing);
    } catch {
      /* l'UI ne doit jamais faire échouer la lecture */
    }
  }
}

/**
 * Joue un son d'Adhan (arrête toute lecture en cours).
 * @param {string} url chemin relatif du MP3 (ex. « /adhan/alafasy.mp3 »)
 * @returns {Promise<void>} résolue au démarrage effectif de la lecture
 */
export function playAdhanSound(url, options = {}) {
  // Arrête et libère la lecture précédente (une seule à la fois).
  stopAdhanSound();
  const audio = new Audio(url);
  audio.preload = 'auto';
  // Volume propre à l'Adhan (0-100), indépendant du lecteur du Coran.
  const target = clampVolume(options.volume);
  audio.volume = options.fadeIn ? 0 : target;
  if (options.fadeIn) fadeIn(audio, target);
  audio.addEventListener('ended', () => {
    if (currentAudio === audio) {
      currentAudio = null;
      notifyStateChange(false);
    }
  });
  audio.addEventListener('error', () => {
    if (currentAudio === audio) {
      currentAudio = null;
      notifyStateChange(false);
    }
  });
  currentAudio = audio;
  notifyStateChange(true);
  return audio.play();
}

/** Volume 0-100 → 0..1 (défaut 1). */
function clampVolume(percent) {
  const n = Number(percent);
  if (!Number.isFinite(n)) return 1;
  return Math.min(1, Math.max(0, n / 100));
}

/** Montée progressive du volume (≈ 4 s) jusqu'à la cible. */
function fadeIn(audio, target, durationMs = 4000) {
  const steps = 20;
  let i = 0;
  const timer = setInterval(() => {
    i += 1;
    if (currentAudio !== audio || i >= steps) {
      clearInterval(timer);
      if (currentAudio === audio) audio.volume = target;
      return;
    }
    audio.volume = target * (i / steps);
  }, durationMs / steps);
}

/** Bip court (Web Audio), pour le mode d'alerte « bip ». */
export function playBeep(volume = 100) {
  try {
    const Ctx = window.AudioContext || window.webkitAudioContext;
    const ctx = new Ctx();
    const osc = ctx.createOscillator();
    const gain = ctx.createGain();
    gain.gain.value = clampVolume(volume) * 0.4;
    osc.frequency.value = 880;
    osc.connect(gain).connect(ctx.destination);
    osc.start();
    osc.stop(ctx.currentTime + 0.35);
    osc.onended = () => ctx.close();
  } catch {
    /* audio indisponible : la notification reste visible */
  }
}

/** Arrête la lecture courante (idempotent). */
export function stopAdhanSound() {
  if (!currentAudio) return;
  const audio = currentAudio;
  currentAudio = null;
  try {
    audio.pause();
    audio.currentTime = 0;
  } catch {
    /* déjà arrêté ou média non chargé */
  }
  notifyStateChange(false);
}

/**
 * Écoute les messages du service worker (notification push → lecture).
 * À appeler UNE fois au montage de l'app (App.vue).
 * Les navigateurs exigent une interaction utilisateur avant de jouer un
 * son : si le navigateur refuse (NotAllowedError), la notification reste
 * affichée sans son — comportement dégradé acceptable.
 */
export function initAdhanPushListener() {
  if (typeof navigator === 'undefined' || !('serviceWorker' in navigator)) return;
  navigator.serviceWorker.addEventListener('message', (event) => {
    const data = event.data;
    if (!data || data.type !== 'PLAY_ADHAN') return;
    if (data.alertMode === 'beep') {
      playBeep(data.volume);
      return;
    }
    if (!data.soundUrl) return;
    // Lecture en aval de l'interaction utilisateur : certaines policies
    // autorisent la lecture car la notification a été affichée par le SW.
    playAdhanSound(data.soundUrl, {
      volume: data.volume,
      fadeIn: data.fadeIn === true,
    }).catch(() => {
      /* autoplay refusé : la notification est visible sans son */
    });
  });
}
