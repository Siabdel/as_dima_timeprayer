// ===========================================================================
// readingStatus : suivi personnel des sourates (statut de lecture / Hifz) et
// récitateurs favoris. Persisté dans le localStorage (fonctionne sans compte).
// ===========================================================================
import { defineStore } from 'pinia';

const STATUS_KEY = 'pc_surah_status';
const FAV_KEY = 'pc_fav_reciters';

/** Statuts proposés ; `value: ''` = aucun statut. `tone` = classe Bootstrap. */
export const SURAH_STATUSES = [
  { value: 'to_read', label: 'À lire', group: 'Lecture', tone: 'secondary' },
  { value: 'reading', label: 'En cours', group: 'Lecture', tone: 'warning' },
  { value: 'read', label: 'Lu', group: 'Lecture', tone: 'success' },
  { value: 'reread', label: 'À relire / Favori', group: 'Lecture', tone: 'info' },
  { value: 'learning', label: 'En apprentissage', group: 'Mémorisation (Hifz)', tone: 'primary' },
  { value: 'memorized', label: 'Mémorisé', group: 'Mémorisation (Hifz)', tone: 'success' },
  { value: 'review', label: 'À réviser', group: 'Mémorisation (Hifz)', tone: 'danger' },
];

const VALID = new Set(SURAH_STATUSES.map((s) => s.value));

function readJson(key, fallback) {
  try {
    const raw = window.localStorage.getItem(key);
    return raw ? JSON.parse(raw) : fallback;
  } catch {
    return fallback;
  }
}

function writeJson(key, value) {
  try {
    window.localStorage.setItem(key, JSON.stringify(value));
  } catch {
    // Stockage indisponible : l'état reste valable pour la session.
  }
}

export const useReadingStatusStore = defineStore('readingStatus', {
  state: () => {
    const stored = readJson(STATUS_KEY, {});
    const statuses = {};
    for (const [k, v] of Object.entries(stored && typeof stored === 'object' ? stored : {})) {
      if (VALID.has(v)) statuses[k] = v;
    }
    const favs = readJson(FAV_KEY, []);
    return {
      /** { [numéro de sourate]: statut } */
      statuses,
      /** Identifiants (id de sons d'Adhan) des récitateurs favoris. */
      favoriteReciters: Array.isArray(favs) ? favs.map(String) : [],
    };
  },
  actions: {
    statusOf(surah) {
      return this.statuses[surah] ?? '';
    },
    setStatus(surah, value) {
      if (VALID.has(value)) this.statuses[surah] = value;
      else delete this.statuses[surah];
      writeJson(STATUS_KEY, this.statuses);
    },
    isFavoriteReciter(id) {
      return this.favoriteReciters.includes(String(id));
    },
    toggleFavoriteReciter(id) {
      const key = String(id);
      this.favoriteReciters = this.isFavoriteReciter(key)
        ? this.favoriteReciters.filter((f) => f !== key)
        : [...this.favoriteReciters, key];
      writeJson(FAV_KEY, this.favoriteReciters);
    },
  },
});
