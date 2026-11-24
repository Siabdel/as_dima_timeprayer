// Configuration du routeur (Vue Router 4, mode history).
import { createRouter, createWebHistory } from 'vue-router';
import { useAuthStore } from '../stores/auth';

import PrayerTimesView from '../views/PrayerTimesView.vue';
import QuranView from '../views/QuranView.vue';
import SurahView from '../views/SurahView.vue';
import ToolsView from '../views/ToolsView.vue';
import CalendarView from '../views/CalendarView.vue';
import LibraryView from '../views/LibraryView.vue';
import SettingsView from '../views/SettingsView.vue';
import LoginView from '../views/LoginView.vue';
import RegisterView from '../views/RegisterView.vue';

const routes = [
  { path: '/', name: 'prayer-times', component: PrayerTimesView },
  { path: '/quran', name: 'quran', component: QuranView },
  // Lecture d'une sourate : /quran/1, /quran/2, ... (étapes 4-5, Coran)
  { path: '/quran/:number', name: 'surah', component: SurahView },
  { path: '/tools', name: 'tools', component: ToolsView },
  // Calendrier des fêtes islamiques et marocaines (public)
  { path: '/calendar', name: 'calendar', component: CalendarView },
  // Cahier de douâas et hadiths du Prophète ﷺ (public)
  { path: '/library', name: 'library', component: LibraryView },
  {
    path: '/settings',
    name: 'settings',
    component: SettingsView,
    // Ouverte à tous : les sections locales (lieu, récitateur, cache audio)
    // fonctionnent sans compte ; le reste est réservé aux comptes.
  },
  {
    path: '/login',
    name: 'login',
    component: LoginView,
    meta: { guestOnly: true },
  },
  {
    path: '/register',
    name: 'register',
    component: RegisterView,
    meta: { guestOnly: true },
  },
  // Route inconnue : retour à l'accueil
  { path: '/:pathMatch(.*)*', redirect: '/' },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

// Garde global :
//  - requiresAuth : non connecté → page de connexion avec mémorisation de la cible ;
//  - guestOnly : déjà connecté → retour à l'accueil.
router.beforeEach((to) => {
  const auth = useAuthStore();

  if (to.meta.requiresAuth && !auth.isAuthenticated) {
    return { name: 'login', query: { redirect: to.fullPath } };
  }
  if (to.meta.guestOnly && auth.isAuthenticated) {
    return '/';
  }
  return true;
});

export default router;
