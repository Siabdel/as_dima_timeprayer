// Store Pinia « preferences » : préférences de notification de l'utilisateur.
// Squelette volontairement minimal — sera complété aux étapes 2-3 du projet
// (formulaire de réglages, mode silencieux, méthode de calcul, etc.).
import { defineStore } from 'pinia';
import client from '../api/client';

export const usePreferencesStore = defineStore('preferences', {
  state: () => ({
    // Préférences courantes, format contrat API :
    // { id, notifications_enabled, fajr, sunrise, dhuhr, asr, maghrib, isha,
    //   quiet_hours_start, quiet_hours_end, calculation_method, madhhab,
    //   default_location }
    preference: null,
    loading: false,
  }),

  actions: {
    /** GET /auth/preferences/ — charge les préférences de l'utilisateur connecté. */
    async fetch() {
      this.loading = true;
      try {
        const response = await client.get('/auth/preferences/');
        this.preference = response.data;
        return this.preference;
      } finally {
        this.loading = false;
      }
    },

    /** PUT /auth/preferences/ — met à jour les préférences puis stocke le résultat. */
    async update(payload) {
      this.loading = true;
      try {
        const response = await client.put('/auth/preferences/', payload);
        this.preference = response.data;
        return this.preference;
      } finally {
        this.loading = false;
      }
    },
  },
});
