<script setup>
// Composant racine : navbar Bootstrap, zone de contenu (router-view) et footer sobre.
// Le lecteur audio du Coran est monté ICI (une seule fois, jamais démonté en
// naviguant) : l'état vit dans le store Pinia « quranPlayer ».
import { computed, onMounted, ref } from 'vue';
import { useRouter } from 'vue-router';
import { useAuthStore } from './stores/auth';
import { useQuranPlayerStore } from './stores/quranPlayer';
import { initAdhanPushListener } from './services/adhanAudio';
import AudioPlayer from './components/AudioPlayer.vue';

const router = useRouter();
const auth = useAuthStore();
const quranPlayer = useQuranPlayerStore();

// Vrai si des tokens sont présents (session considérée active).
const isAuthenticated = computed(() => auth.isAuthenticated);

// Déconnexion : purge du store puis retour à la page de connexion.
function handleLogout() {
  auth.logout();
  router.push({ name: 'login' });
}

// Élément <audio> unique de l'application : rendu au niveau racine, il
// persiste en naviguant. Le store s'y attache une fois au montage.
const audioEl = ref(null);
onMounted(() => {
  quranPlayer.attachAudioElement(audioEl.value);
  // Notifications push : le service worker transmet { type: 'PLAY_ADHAN',
  // soundUrl } — on joue le son d'Adhan dans cette fenêtre (un SW ne peut
  // pas jouer d'audio lui-même). Aucun effet hors notifications Adhan.
  initAdhanPushListener();
});
</script>

<template>
  <div class="d-flex flex-column min-vh-100">
    <!-- Navigation principale -->
    <nav
      class="navbar navbar-expand-md navbar-dark bg-pc-green shadow-sm"
      aria-label="Navigation principale"
    >
      <div class="container">
        <router-link class="navbar-brand fw-bold" to="/">
          <span aria-hidden="true">🕌</span> Prière &amp; Coran
        </router-link>

        <!-- Bouton burger (mobile), piloté par le JS de Bootstrap -->
        <button
          class="navbar-toggler"
          type="button"
          data-bs-toggle="collapse"
          data-bs-target="#main-nav"
          aria-controls="main-nav"
          aria-expanded="false"
          aria-label="Basculer la navigation"
        >
          <span class="navbar-toggler-icon"></span>
        </button>

        <div id="main-nav" class="collapse navbar-collapse">
          <!-- Liens principaux -->
          <ul class="navbar-nav me-auto">
            <li class="nav-item">
              <router-link class="nav-link" to="/">Horaires</router-link>
            </li>
            <li class="nav-item">
              <router-link class="nav-link" to="/quran">Coran</router-link>
            </li>
            <li class="nav-item">
              <router-link class="nav-link" to="/tools">Outils</router-link>
            </li>
            <li class="nav-item">
              <router-link class="nav-link" to="/calendar">Calendrier</router-link>
            </li>
            <li class="nav-item">
              <router-link class="nav-link" to="/library">Douâa &amp; Hadiths</router-link>
            </li>
            <!-- Réglages : visible uniquement si connecté -->
            <li v-if="isAuthenticated" class="nav-item">
              <router-link class="nav-link" to="/settings">Réglages</router-link>
            </li>
          </ul>

          <!-- Zone de session -->
          <ul class="navbar-nav align-items-md-center">
            <template v-if="!isAuthenticated">
              <li class="nav-item">
                <router-link class="nav-link" to="/login">Connexion</router-link>
              </li>
              <li class="nav-item">
                <router-link class="nav-link" to="/register">Inscription</router-link>
              </li>
            </template>
            <template v-else>
              <li class="nav-item">
                <span class="navbar-text pc-nav-email me-md-2" :title="auth.user?.email">
                  {{ auth.user?.email }}
                </span>
              </li>
              <li class="nav-item mt-2 mt-md-0">
                <button class="btn btn-outline-light btn-sm" type="button" @click="handleLogout">
                  Déconnexion
                </button>
              </li>
            </template>
          </ul>
        </div>
      </div>
    </nav>

    <!-- Contenu des pages -->
    <main class="container py-4 flex-grow-1">
      <router-view />
    </main>

    <!-- Footer sobre : aucun suivi, aucune publicité -->
    <footer class="pc-footer py-3 text-center">
      <small>Prière &amp; Coran — sans publicité, respectueux de votre vie privée</small>
    </footer>

    <!-- Lecteur audio du Coran : barre fixe en bas, visible pendant la lecture.
         L'état vit dans le store → la lecture continue d'une page à l'autre. -->
    <AudioPlayer v-if="quranPlayer.audioUrl" />

    <!-- Élément <audio> UNIQUE de l'application : invisible, rendu au niveau
         racine (jamais démonté en naviguant), piloté par le store. -->
    <audio ref="audioEl" preload="metadata" class="d-none"></audio>
  </div>
</template>
