// Store Pinia « auth » : session utilisateur (profil + tokens JWT).
import { defineStore } from 'pinia';
import * as authApi from '../api/auth';
import { getTokens, setTokens, clearTokens } from '../api/client';

export const useAuthStore = defineStore('auth', {
  state: () => ({
    user: null, // { id, email, first_name, last_name }
    tokens: getTokens(), // { access, refresh } | null
  }),

  getters: {
    /** Vrai si un access token est présent (session considérée active). */
    isAuthenticated: (state) => Boolean(state.tokens?.access),
  },

  actions: {
    /**
     * Connexion : récupère les tokens, les persiste, puis charge le profil.
     * @param {string} email
     * @param {string} password
     */
    async login(email, password) {
      const tokens = await authApi.login(email, password);
      setTokens(tokens);
      this.tokens = tokens;
      await this.fetchMe();
      return this.user;
    },

    /**
     * Inscription puis connexion automatique avec les mêmes identifiants.
     * @param {{ email: string, password: string, password2: string,
     *           first_name?: string, last_name?: string }} payload
     */
    async register(payload) {
      await authApi.register(payload);
      return this.login(payload.email, payload.password);
    },

    /** Charge (ou recharge) le profil de l'utilisateur connecté. */
    async fetchMe() {
      this.user = await authApi.me();
      return this.user;
    },

    /** Déconnexion : purge des tokens et du profil. */
    logout() {
      clearTokens();
      this.tokens = null;
      this.user = null;
    },
  },
});

// Écoute l'événement global « auth:logout » émis par l'intercepteur Axios
// quand le refresh token n'est plus utilisable : on aligne l'état du store.
// Enregistré une seule fois, au niveau du module du store.
if (typeof window !== 'undefined') {
  window.addEventListener('auth:logout', () => {
    const auth = useAuthStore();
    auth.tokens = null;
    auth.user = null;
  });
}
