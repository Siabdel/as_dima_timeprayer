// ===========================================================================
// Store Pinia « prayerTimes » : horaires de prière, lieu, méthode, madhhab.
// ---------------------------------------------------------------------------
// - Le lieu/method/madhhab sont persistés dans le localStorage (clé
//   « pc_prayer_location ») pour les visiteurs non connectés ;
// - fetchToday() gère le cas 400 « no_default_location » avec un message
//   d'erreur en français.
// ===========================================================================
import { defineStore } from 'pinia';
import { getPrayerTimes, getTodayPrayerTimes } from '../api/prayerTimes';

/** Clé de persistance locale (lieu + méthode + madhhab). */
const STORAGE_KEY = 'pc_prayer_location';

/** Message français pour l'erreur métier « no_default_location ». */
const NO_DEFAULT_LOCATION_MESSAGE =
  'Aucun lieu par défaut défini. Choisissez votre lieu pour afficher les horaires de prière.';

/**
 * Lit les données persistées dans le localStorage (silencieux si absent).
 * @returns {{ location?: Object, method?: number, madhhab?: string } | null}
 */
function readPersisted() {
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    return raw ? JSON.parse(raw) : null;
  } catch {
    // JSON invalide ou localStorage indisponible.
    return null;
  }
}

/** Construit les paramètres de requête correspondant à un lieu. */
function locationParams(location) {
  if (!location) return {};
  if (location.latitude != null && location.longitude != null) {
    return { latitude: location.latitude, longitude: location.longitude };
  }
  return { city: location.city, country: location.country };
}

export const usePrayerTimesStore = defineStore('prayerTimes', {
  state: () => ({
    /** Dernière réponse API complète (timings, hijri_date, timezone, stale...). */
    data: null,
    loading: false,
    /** Erreur brute Axios ou { message, code } normalisée (erreur métier). */
    error: null,
    /** { latitude, longitude } ou { city, country } */
    location: null,
    /** Date des horaires affichés (« YYYY-MM-DD », renvoyée par l'API). */
    date: null,
    /** Méthode de calcul (0-30, défaut 3 = Muslim World League). */
    method: 3,
    /** École juridique (« standard » | « hanafi »). */
    madhhab: 'standard',
  }),

  actions: {
    /**
     * Restaure method/madhhab/location depuis le localStorage
     * (appelé au montage de la vue, avant toute requête).
     */
    restorePersisted() {
      const saved = readPersisted();
      if (!saved) return;
      if (typeof saved.method === 'number') this.method = saved.method;
      if (saved.madhhab === 'standard' || saved.madhhab === 'hanafi') {
        this.madhhab = saved.madhhab;
      }
      if (saved.location && typeof saved.location === 'object') {
        this.location = saved.location;
      }
    },

    /**
     * Persiste method/madhhab/location dans le localStorage
     * (utile pour les visiteurs non connectés ; inoffensif pour les autres).
     */
    persistState() {
      try {
        window.localStorage.setItem(
          STORAGE_KEY,
          JSON.stringify({
            location: this.location,
            method: this.method,
            madhhab: this.madhhab,
          })
        );
      } catch {
        // localStorage indisponible : on ignore silencieusement.
      }
    },

    /**
     * GET /prayer-times/ — récupère les horaires selon les paramètres fournis.
     * Les paramètres explicites (location/method/madhhab) écrasent l'état,
     * qui est ensuite préservé pour les requêtes suivantes.
     * @param {Object} params { latitude, longitude } | { city, country },
     *        date, method, madhhab
     */
    async fetch(params = {}) {
      // Mise à jour de l'état avec les paramètres explicites.
      if (params.latitude != null && params.longitude != null) {
        this.location = { latitude: params.latitude, longitude: params.longitude };
      } else if (params.city) {
        this.location = { city: params.city, country: params.country ?? '' };
      }
      if (params.method != null) this.method = params.method;
      if (params.madhhab) this.madhhab = params.madhhab;

      const query = { method: this.method, madhhab: this.madhhab };
      if (params.date) query.date = params.date;
      Object.assign(query, locationParams(this.location));

      this.loading = true;
      this.error = null;
      try {
        const response = await getPrayerTimes(query);
        this.data = response.data;
        this.date = response.data?.date ?? null;
        this.persistState();
        return this.data;
      } catch (error) {
        this.error = error;
        throw error;
      } finally {
        this.loading = false;
      }
    },

    /**
     * GET /prayer-times/today/ — horaires du jour pour le lieu par défaut
     * du serveur (utilisateur connecté). En cas de 400 « no_default_location »,
     * l'erreur est normalisée avec un message en français.
     */
    async fetchToday() {
      this.loading = true;
      this.error = null;
      try {
        const response = await getTodayPrayerTimes({
          method: this.method,
          madhhab: this.madhhab,
        });
        this.data = response.data;
        this.date = response.data?.date ?? null;
        // Le backend renvoie le lieu utilisé : on l'aligne avec l'état local.
        if (response.data?.location && typeof response.data.location === 'object') {
          this.location = response.data.location;
        }
        this.persistState();
        return this.data;
      } catch (error) {
        const code = error?.response?.data?.error?.code;
        if (error?.response?.status === 400 && code === 'no_default_location') {
          // Erreur métier attendue : message actionnable en français.
          this.error = { message: NO_DEFAULT_LOCATION_MESSAGE, code };
        } else {
          this.error = error;
        }
        throw error;
      } finally {
        this.loading = false;
      }
    },

    /**
     * Définit le lieu courant (coordonnées ou ville/pays), le persiste,
     * puis recharge immédiatement les horaires correspondants.
     * @param {{ latitude: number, longitude: number } | { city: string, country: string }} location
     */
    async setLocation(location) {
      if (!location || typeof location !== 'object') return;
      this.location = location;
      this.persistState();
      // Recharge avec les paramètres explicites du nouveau lieu.
      return this.fetch(locationParams(location));
    },
  },
});
