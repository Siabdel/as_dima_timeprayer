// ===========================================================================
// Store Pinia « quranPlayer » : lecteur audio du Coran, PERSISTANT entre les
// pages.
// ---------------------------------------------------------------------------
// - L'élément <audio> unique est rendu par App.vue (jamais démonté en
//   naviguant) et attaché au store via attachAudioElement() ;
// - L'état (sourate, verset, URL, temps) vit ici : la barre AudioPlayer et
//   les listes (surlignage) réagissent au store ;
// - Le récitateur choisi est persisté dans le localStorage (« pc_reciter_id ») ;
// - Chaque lancement passe par l'API : audio chapitre ou audio verset.
// ===========================================================================
import { defineStore } from 'pinia';
import { getChapterAudio, getVerseAudio, getReciters } from '../api/quran';

/** Clé de persistance du récitateur choisi. */
const RECITER_KEY = 'pc_reciter_id';

/** Clé de persistance du mode de lecture « mot à mot ». */
const WORD_MODE_KEY = 'pc_word_mode';

/** Récitateur par défaut (id 7 = Mishary Alafasy dans le contrat API). */
const DEFAULT_RECITER_ID = 7;

/**
 * Élément <audio> unique de l'application, hors state Pinia (un nœud DOM n'a
 * rien à faire dans un store réactif). Rempli par attachAudioElement().
 */
let audioEl = null;

/**
 * Élément <audio> DÉDIÉ à la séquence mot à mot. Volontairement distinct du
 * lecteur de sourate : les mots sont des MP3 très courts, enchaînés par
 * programme, et ne doivent ni toucher la barre de lecture ni sa position.
 */
let wordAudioEl = null;

/** Vrai pendant une séquence mot à mot (garde anti-réentrance). */
let wordSequenceRunning = false;

/** Jeton de séquence : incrémenté à chaque démarrage/arrêt (annule l'ancienne). */
let wordSequenceToken = 0;

/**
 * Lit le mode mot à mot persisté (localStorage) avec repli sur false.
 * @returns {boolean}
 */
function readStoredWordMode() {
  try {
    return window.localStorage.getItem(WORD_MODE_KEY) === 'true';
  } catch {
    // localStorage indisponible (navigation privée stricte, etc.).
    return false;
  }
}

/**
 * Lit le récitateur persisté (localStorage) avec repli sur la valeur par défaut.
 * @returns {number}
 */
function readStoredReciter() {
  try {
    const raw = window.localStorage.getItem(RECITER_KEY);
    const id = raw === null ? Number.NaN : Number.parseInt(raw, 10);
    return Number.isInteger(id) && id > 0 ? id : DEFAULT_RECITER_ID;
  } catch {
    // localStorage indisponible (navigation privée stricte, etc.).
    return DEFAULT_RECITER_ID;
  }
}

export const useQuranPlayerStore = defineStore('quranPlayer', {
  state: () => ({
    /** Numéro de la sourate en cours de lecture (ou null). */
    currentSurah: null,
    /** Numéro du verset en cours (null = lecture de la sourate entière). */
    currentAyah: null,
    /** URL audio chargée (null = lecteur masqué). */
    audioUrl: null,
    /** Récitateur sélectionné, persisté dans le localStorage. */
    reciterId: readStoredReciter(),
    /** Vrai tant que l'audio joue. */
    playing: false,
    /** Vrai pendant la récupération d'une URL audio. */
    loading: false,
    /** Position de lecture (secondes). */
    currentTime: 0,
    /** Durée totale (secondes, 0 tant qu'inconnue). */
    duration: 0,
    /** Cache des récitateurs (réponse de /quran/reciters/ → clé « chapter »). */
    reciters: [],
    /** Message d'erreur lisible (échec réseau, lecture impossible...). */
    error: null,
    /** Mode « mot à mot » activé (persisté dans le localStorage). */
    wordByWordMode: readStoredWordMode(),
    /** Mot en cours par verset : { [ayahNumber]: index } (mode mot à mot). */
    activeWordIndex: {},
    /** File de lecture mot à mot : [{ word, ayah, index }, ...]. */
    wordsQueue: [],
    /** Position courante dans wordsQueue (-1 = aucune séquence). */
    wordsQueuePosition: -1,
    /** Numéro de verset en cours de séquence mot à mot (null si aucune). */
    wordsSurah: null,
  }),

  getters: {
    /** Vrai si la lecture en cours est un verset isolé (et non la sourate). */
    isVerseMode: (state) => state.currentAyah !== null,
    /** Libellé lisible de la lecture en cours, ex. « Sourate 2 · verset 255 ». */
    currentLabel: (state) => {
      if (state.currentSurah === null) return '';
      const base = `Sourate ${state.currentSurah}`;
      return state.currentAyah !== null
        ? `${base} · verset ${state.currentAyah}`
        : base;
    },
    /** Vrai si une séquence mot à mot est en cours de lecture. */
    isWordSequencePlaying: (state) => state.wordsQueuePosition >= 0,
    /** Libellé de la séquence, ex. « Sourate 1 · verset 2 · mot 3 ». */
    wordSequenceLabel: (state) => {
      if (state.wordsSurah === null || state.wordsQueuePosition < 0) return '';
      const entry = state.wordsQueue[state.wordsQueuePosition];
      if (!entry) return `Sourate ${state.wordsSurah} - mot a mot`;
      return `Sourate ${state.wordsSurah} - verset ${entry.ayah} - mot ${
        entry.index + 1
      }`;
    },
  },

  actions: {
    /**
     * Attache l'unique élément <audio> (rendu par App.vue) et câble ses
     * événements vers le store. Sans effet si déjà attaché.
     * @param {HTMLAudioElement} el
     */
    attachAudioElement(el) {
      if (!el || audioEl === el) return;
      audioEl = el;
      // Les flèches capturent `this` (l'instance du store) une seule fois.
      el.addEventListener('timeupdate', () => {
        this.currentTime = el.currentTime || 0;
      });
      el.addEventListener('loadedmetadata', () => {
        this.duration = Number.isFinite(el.duration) ? el.duration : 0;
      });
      el.addEventListener('durationchange', () => {
        this.duration = Number.isFinite(el.duration) ? el.duration : 0;
      });
      el.addEventListener('play', () => {
        this.playing = true;
      });
      el.addEventListener('pause', () => {
        this.playing = false;
      });
      el.addEventListener('ended', () => {
        this.playing = false;
      });
      el.addEventListener('error', () => {
        // Ignore les « erreurs » provoquées par stop() (src vide).
        if (!el.getAttribute('src')) return;
        this.playing = false;
        this.error = 'Lecture audio impossible (réseau ou format).';
      });
    },

    /**
     * Sélectionne et persiste le récitateur.
     * @param {number|string} id
     */
    setReciter(id) {
      const parsed = Number.parseInt(id, 10);
      if (!Number.isInteger(parsed) || parsed <= 0) return;
      this.reciterId = parsed;
      try {
        window.localStorage.setItem(RECITER_KEY, String(parsed));
      } catch {
        // Persistance indisponible : le choix reste valable pour la session.
      }
    },

    /**
     * Charge (une seule fois) la liste des récitateurs pour le sélecteur.
     * @returns {Promise<Array>} [{ id, name, style }, ...]
     */
    async fetchReciters() {
      if (this.reciters.length) return this.reciters;
      try {
        const { data } = await getReciters();
        this.reciters = Array.isArray(data?.chapter) ? data.chapter : [];
      } catch {
        // Sélecteur vide en cas d'échec : la lecture reste possible.
        this.reciters = [];
      }
      return this.reciters;
    },

    /**
     * Joue une sourate complète (audio « chapitre »).
     * - Si la même sourate est déjà chargée en mode chapitre : simple
     *   bascule lecture/pause (évite de repartir du début) ;
     * - Sinon : récupère l'URL puis lance la lecture.
     * @param {number|string} surah
     * @param {number|string} [reciterId] optionnel, sinon valeur du store
     */
    async playSurah(surah, reciterId) {
      const surahNumber = Number(surah);
      if (
        this.currentSurah === surahNumber &&
        this.currentAyah === null &&
        this.audioUrl
      ) {
        return this.toggle();
      }
      if (reciterId !== undefined) this.setReciter(reciterId);
      // Marque la cible AVANT la requête : les réponses obsolètes sont ignorées.
      this.currentSurah = surahNumber;
      this.currentAyah = null;
      this.error = null;
      this.loading = true;
      try {
        const { data } = await getChapterAudio(surahNumber, this.reciterId);
        if (this.currentSurah !== surahNumber || this.currentAyah !== null) return;
        await this._playUrl(data?.audio_url);
      } catch {
        this.error = "Impossible de récupérer l'audio de la sourate.";
        this.playing = false;
      } finally {
        this.loading = false;
      }
    },

    /**
     * Joue un verset isolé (audio « verset », timings inclus côté API).
     * - Si le même verset est déjà chargé : bascule lecture/pause ;
     * - Sinon : récupère l'URL puis lance la lecture.
     * @param {number|string} surah
     * @param {number|string} ayah
     * @param {number|string} [reciterId] optionnel, sinon valeur du store
     */
    async playVerse(surah, ayah, reciterId) {
      const surahNumber = Number(surah);
      const ayahNumber = Number(ayah);
      if (
        this.currentSurah === surahNumber &&
        this.currentAyah === ayahNumber &&
        this.audioUrl
      ) {
        return this.toggle();
      }
      if (reciterId !== undefined) this.setReciter(reciterId);
      this.currentSurah = surahNumber;
      this.currentAyah = ayahNumber;
      this.error = null;
      this.loading = true;
      try {
        const { data } = await getVerseAudio(surahNumber, ayahNumber, this.reciterId);
        if (this.currentSurah !== surahNumber || this.currentAyah !== ayahNumber) return;
        await this._playUrl(data?.audio_url);
      } catch {
        this.error = "Impossible de récupérer l'audio du verset.";
        this.playing = false;
      } finally {
        this.loading = false;
      }
    },

    /**
     * Bascule lecture/pause de la source actuellement chargée.
     * Sans effet si rien n'est chargé.
     */
    toggle() {
      if (!audioEl || !this.audioUrl) return;
      if (this.playing) {
        audioEl.pause();
      } else {
        audioEl.play().catch(() => {
          // Lecture refusée (autoplay, média introuvable) : on aligne l'état.
          this.playing = false;
        });
      }
    },

    /**
     * Met en pause sans perdre la position (le lecteur reste affiché).
     */
    pause() {
      if (audioEl && this.audioUrl) audioEl.pause();
    },

    /**
     * Stoppe tout : pause, purge de la source et remise à zéro de l'état
     * (la barre du lecteur disparaît).
     */
    stop() {
      if (audioEl) {
        audioEl.pause();
        audioEl.removeAttribute('src');
        try {
          audioEl.load(); // réinitialise l'élément après purge de la source
        } catch {
          // load() sur un élément sans source ne doit jamais casser l'UI.
        }
      }
      this.playing = false;
      this.currentTime = 0;
      this.duration = 0;
      this.audioUrl = null;
      this.currentSurah = null;
      this.currentAyah = null;
    },

    /**
     * Met à jour la position consultée (sans toucher à la lecture).
     * Utilisé pour le suivi de progression / le surlignage.
     * @param {number} surah
     * @param {number|null} ayah
     */
    setCurrentAyah(surah, ayah) {
      this.currentSurah = surah;
      this.currentAyah = ayah;
    },

    /**
     * Déplace la position de lecture (barre de progression).
     * @param {number} time secondes
     */
    seek(time) {
      if (!audioEl) return;
      const t = Number(time);
      if (!Number.isFinite(t) || t < 0) return;
      audioEl.currentTime = t;
      this.currentTime = t;
    },

    /**
     * Recharge la lecture en cours avec le récitateur choisi
     * (appelé après un changement de récitateur pendant la lecture).
     */
    async reloadCurrent() {
      if (this.currentSurah === null || !this.audioUrl) return;
      const surah = this.currentSurah;
      const ayah = this.currentAyah;
      const wasPlaying = this.playing;
      this.loading = true;
      this.error = null;
      try {
        const { data } =
          ayah !== null
            ? await getVerseAudio(surah, ayah, this.reciterId)
            : await getChapterAudio(surah, this.reciterId);
        const url = data?.audio_url;
        if (!url || !audioEl) return;
        this.audioUrl = url;
        audioEl.src = url;
        audioEl.load();
        this.currentTime = 0;
        this.duration = 0;
        if (wasPlaying) {
          await audioEl.play().catch(() => {
            this.playing = false;
          });
        }
      } catch {
        this.error = 'Impossible de changer de récitateur.';
      } finally {
        this.loading = false;
      }
    },

    /**
     * Affecte l'URL au lecteur et lance la lecture (usage interne).
     * @param {string} url
     */
    async _playUrl(url) {
      if (!url || !audioEl) {
        this.error = "Aucune URL audio disponible pour cette lecture.";
        return;
      }
      // Nouvelle source uniquement si différente (évite de rejouer au clic pause).
      if (audioEl.getAttribute('src') !== url) {
        audioEl.src = url;
        audioEl.load();
        this.currentTime = 0;
        this.duration = 0;
      }
      this.audioUrl = url;
      try {
        await audioEl.play();
        this.playing = true;
      } catch {
        this.playing = false;
      }
    },

    // =======================================================================
    // Lecture « mot à mot »
    // -----------------------------------------------------------------------
    // Les mots isolés sont joués par un élément Audio DÉDIÉ (jamais celui de
    // la sourate) : le <audio> global et sa barre de progression restent
    // intacts, et l'état `playing` du store reste la source de vérité.
    // =======================================================================

    /**
     * Active/désactive le mode mot à mot et le persiste (localStorage).
     * La désactivation arrête aussi la séquence en cours.
     * @param {boolean} value
     */
    setWordByWordMode(value) {
      const on = Boolean(value);
      this.wordByWordMode = on;
      try {
        window.localStorage.setItem(WORD_MODE_KEY, on ? 'true' : 'false');
      } catch {
        // Persistance indisponible : le mode reste valable pour la session.
      }
      if (!on) this.stopWordsSequence();
    },

    /**
     * Construit la file de mots d'une liste de versets (hors marqueurs de fin
     * de verset, et hors mots sans audio disponible).
     * @param {Array} verses versets portant un tableau `words`
     * @returns {Array<{word: Object, ayah: number, index: number}>}
     */
    _buildWordsQueue(verses) {
      const queue = [];
      for (const verse of Array.isArray(verses) ? verses : []) {
        const ayah = Number(verse?.ayah_number);
        if (!Number.isInteger(ayah)) continue;
        const words = Array.isArray(verse?.words) ? verse.words : [];
        words.forEach((word, index) => {
          // is_end = marqueur « fin de verset » : jamais surligné ni joué.
          if (!word || word.is_end === true) return;
          // Sans URL audio, le mot est affiché mais ne peut pas être joué.
          if (!word.audio_url) return;
          queue.push({ word, ayah, index });
        });
      }
      return queue;
    },

    /**
     * Lance la lecture mot à mot d'une liste de versets.
     * @param {Array} verses versets avec `words` (GET ...?words=true)
     * @param {number} [startAt] position de départ dans la file (défaut 0)
     * @param {number|string} [surah] numéro de sourate (pour le libellé)
     */
    playWordsSequence(verses, startAt = 0, surah = null) {
      const queue = this._buildWordsQueue(verses);
      this.wordsQueue = queue;
      if (!queue.length) {
        this.error = 'Aucun mot audio disponible pour cette sourate.';
        this._teardownWordAudio();
        this.wordsQueuePosition = -1;
        this.wordsSurah = null;
        return;
      }
      this.wordsSurah = this._surahOf(surah ?? verses);
      // La lecture normale (sourate / verset) laisse la place à la séquence.
      this.pause();
      this._runWordsQueue(this._clampQueueIndex(startAt));
    },

    /**
     * Reprend la séquence mot à mot À PARTIR d'un mot cliqué
     * (verset + index du mot dans le verset).
     * @param {Array} verses versets avec `words`
     * @param {number|string} ayah numéro du verset cliqué
     * @param {number|string} index index du mot dans le verset cliqué
     * @param {number|string} [surah] numéro de sourate (pour le libellé)
     */
    playWordsFrom(verses, ayah, index, surah = null) {
      const queue = this.wordsQueue.length
        ? this.wordsQueue
        : this._buildWordsQueue(verses);
      const ayahNumber = Number(ayah);
      const wordIndex = Number(index);
      const position = queue.findIndex(
        (entry) => entry.ayah === ayahNumber && entry.index === wordIndex
      );
      if (position < 0) {
        // Mot inconnu (sans audio) : on repart simplement du début.
        this.playWordsSequence(verses, 0, surah);
        return;
      }
      this.wordsQueue = queue;
      this.wordsSurah = this._surahOf(surah ?? verses);
      this.pause();
      this._runWordsQueue(position);
    },

    /**
     * Arrête la séquence mot à mot (le lecteur de sourate n'est pas touché).
     */
    stopWordsSequence() {
      // Nouveau jeton : toute boucle en cours s'arrête au prochain tour.
      wordSequenceToken += 1;
      wordSequenceRunning = false;
      this._teardownWordAudio();
      this.wordsQueuePosition = -1;
      this.wordsQueue = [];
      this.wordsSurah = null;
      this.activeWordIndex = {};
      // L'état de lecture reflète la fin de la séquence de mots.
      this.playing = false;
      this.error = null;
    },

    /**
     * Libère l'élément Audio dédié à la séquence mot à mot (usage interne).
     */
    _teardownWordAudio() {
      if (!wordAudioEl) return;
      try {
        wordAudioEl.onended = null;
        wordAudioEl.onerror = null;
        wordAudioEl.pause();
        wordAudioEl.removeAttribute('src');
        wordAudioEl.load();
      } catch {
        // La libération ne doit jamais casser l'UI.
      }
      wordAudioEl = null;
    },

    /**
     * Détermine le numéro de sourate d'une séquence (usage interne).
     * Accepte soit un numéro explicite (fourni par la vue), soit une liste de
     * versets — le contrat API des versets n'expose pas `surah_number`, le
     * champ est donc optionnel ici.
     * @param {number|string|Array} source numéro de sourate ou liste de versets
     * @returns {number|null}
     */
    _surahOf(source) {
      if (Array.isArray(source)) {
        const first = source[0];
        const value = Number(first?.surah_number ?? first?.surah ?? Number.NaN);
        return Number.isInteger(value) ? value : null;
      }
      const value = Number(source);
      return Number.isInteger(value) && value > 0 ? value : null;
    },

    /**
     * Borne un index de file dans [0, length - 1] (usage interne).
     * @param {number} index
     * @returns {number}
     */
    _clampQueueIndex(index) {
      const n = Number.parseInt(index, 10);
      if (!Number.isInteger(n) || n < 0) return 0;
      return Math.min(n, Math.max(0, this.wordsQueue.length - 1));
    },

    /**
     * Boucle de lecture séquentielle : un mot à la fois, puis le suivant à
     * l'événement « ended ». Un mot en erreur est sauté (la séquence continue).
     * @param {number} startIndex position de départ dans wordsQueue
     */
    async _runWordsQueue(startIndex) {
      wordSequenceToken += 1;
      const token = wordSequenceToken;
      wordSequenceRunning = true;
      this.error = null;

      for (let i = startIndex; i < this.wordsQueue.length; i += 1) {
        // Séquence arrêtée ou remplacée entre-temps : on sort proprement.
        if (token !== wordSequenceToken) return;
        const entry = this.wordsQueue[i];
        this.wordsQueuePosition = i;
        this.activeWordIndex = { [entry.ayah]: entry.index };

        const ok = await this._playWord(entry.word.audio_url, token);
        if (token !== wordSequenceToken) return;
        if (!ok) continue; // mot illisible : on passe au suivant
      }

      if (token !== wordSequenceToken) return;
      // Fin de séquence : on nettoie l'état (plus aucun mot surligné).
      wordSequenceRunning = false;
      this._teardownWordAudio();
      this.wordsQueuePosition = -1;
      this.wordsQueue = [];
      this.wordsSurah = null;
      this.activeWordIndex = {};
      this.playing = false;
    },

    /**
     * Joue UN mot isolé et résout à la fin de sa lecture (usage interne).
     * Utilise un Audio dédié, jamais le <audio> de la sourate.
     * @param {string} url URL absolue du MP3 du mot
     * @param {number} token jeton de séquence (annulation)
     * @returns {Promise<boolean>} vrai si le mot a été joué jusqu'au bout
     */
    _playWord(url, token) {
      return new Promise((resolve) => {
        if (!url) {
          resolve(false);
          return;
        }
        const el = new Audio(url);
        el.preload = 'auto';
        wordAudioEl = el;

        let settled = false;
        const finish = (ok) => {
          if (settled) return;
          settled = true;
          el.onended = null;
          el.onerror = null;
          if (wordAudioEl === el) wordAudioEl = null;
          resolve(ok);
        };

        el.onended = () => finish(true);
        // Fichier introuvable / réseau : on saute le mot et on continue.
        el.onerror = () => finish(false);

        this.playing = true;
        const played = el.play();
        if (played && typeof played.catch === 'function') {
          played.catch(() => finish(false));
        }

        // Séquence arrêtée pendant ce mot : on résout sans boucler plus loin.
        const watchdog = setInterval(() => {
          if (token !== wordSequenceToken) {
            clearInterval(watchdog);
            try {
              el.pause();
            } catch {
              // Pause impossible : l'élément est déjà détruit.
            }
            finish(false);
          }
        }, 200);
        const clear = () => clearInterval(watchdog);
        el.addEventListener('ended', clear, { once: true });
        el.addEventListener('error', clear, { once: true });
      });
    },
  },
});
