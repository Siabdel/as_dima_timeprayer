<script setup>
// ===========================================================================
// AudioPlayer : barre de lecture fixe en bas de page.
// ---------------------------------------------------------------------------
// - Montée UNE FOIS dans App.vue (v-if="quranPlayer.audioUrl") : l'élément
//   <audio>, lui, vit au niveau racine et n'est jamais démonté en naviguant ;
// - Play/pause (bouton natif : Entrée / Espace au clavier, focus visible),
//   barre de progression (input range), temps mm:ss, titre de la lecture
//   en cours (aria-live="polite"), sélecteur de récitateur (persisté),
//   bouton fermer (= stop) ;
// - Le changement de récitateur recharge la lecture en cours s'il y en a une.
// ===========================================================================
import { computed, onMounted, onBeforeUnmount, watch } from 'vue';
import { useQuranPlayerStore } from '../stores/quranPlayer';

const props = defineProps({
  /**
   * Liste des récitateurs (réponse de /quran/reciters/ → clé « chapter »).
   * Si vide, le composant charge et met en cache via le store.
   */
  reciters: { type: Array, default: () => [] },
});

const player = useQuranPlayerStore();

// Liste affichée : prop prioritaire, sinon cache du store (chargé au montage).
const reciterOptions = computed(() =>
  props.reciters.length ? props.reciters : player.reciters
);

/** Temps formaté « mm:ss » (ou « --:-- » si inconnu). */
function formatTime(seconds) {
  if (!Number.isFinite(seconds) || seconds < 0) return '--:--';
  const total = Math.floor(seconds);
  const minutes = Math.floor(total / 60);
  const secs = total % 60;
  return `${String(minutes).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;
}

const currentTimeLabel = computed(() => formatTime(player.currentTime));
const durationLabel = computed(() =>
  player.duration > 0 ? formatTime(player.duration) : '--:--'
);

/** Progression en % pour la largeur remplie de la barre (accessibilité/style). */
const progressPercent = computed(() =>
  player.duration > 0
    ? Math.min(100, Math.round((player.currentTime / player.duration) * 100))
    : 0
);

/** Déplacement dans la barre de progression. */
function onSeek(event) {
  const value = Number.parseFloat(event.target.value);
  if (Number.isFinite(value)) player.seek(value);
}

/** Changement de récitateur : persistance + rechargement de la lecture. */
function onReciterChange(event) {
  player.setReciter(event.target.value);
  if (player.audioUrl) player.reloadCurrent();
}

// Réserve de place sous la barre fixe (le contenu et le footer restent lisibles).
watch(
  () => player.audioUrl,
  (url) => {
    if (typeof document !== 'undefined') {
      document.body.classList.toggle('pc-audio-player-open', Boolean(url));
    }
  },
  { immediate: true }
);

// Charge les récitateurs une seule fois (si la prop n'en fournit pas).
onMounted(() => {
  if (!reciterOptions.value.length) player.fetchReciters();
});

onBeforeUnmount(() => {
  if (typeof document !== 'undefined') {
    document.body.classList.remove('pc-audio-player-open');
  }
});
</script>

<template>
  <aside
    class="pc-audio-player"
    role="region"
    aria-label="Lecteur audio du Coran"
  >
    <div class="d-flex align-items-center gap-2 gap-md-3 flex-wrap flex-md-nowrap">
      <!-- Lecture / pause : bouton natif (Entrée / Espace, focus visible) -->
      <button
        class="btn pc-player-btn pc-player-btn-main"
        type="button"
        :aria-label="player.playing ? 'Mettre en pause la lecture' : 'Reprendre la lecture'"
        :disabled="player.loading && !player.audioUrl"
        @click="player.toggle()"
      >
        <span
          v-if="player.loading"
          class="spinner-border spinner-border-sm"
          role="status"
          aria-hidden="true"
        ></span>
        <i
          v-else
          class="bi"
          :class="player.playing ? 'bi-pause-fill' : 'bi-play-fill'"
          aria-hidden="true"
        ></i>
      </button>

      <!-- Titre de la lecture en cours : annoncé poliment aux lecteurs d'écran -->
      <div class="pc-player-title flex-grow-1 min-w-0">
        <span class="aria-live-wrapper" aria-live="polite">
          <span class="pc-player-label">
            {{ player.currentLabel || 'Lecture' }}
          </span>
        </span>
        <small v-if="player.info && !player.error" class="d-block text-muted">
          {{ player.info }}
        </small>
        <small v-if="player.error" class="pc-player-error d-block">
          {{ player.error }}
        </small>
      </div>

      <!-- Progression : temps courant / total + curseur -->
      <div class="pc-player-progress flex-grow-1">
        <input
          type="range"
          class="form-range pc-player-range"
          min="0"
          :max="player.duration > 0 ? player.duration : 1"
          step="0.1"
          :value="player.currentTime"
          :disabled="player.duration <= 0"
          :aria-valuetext="`${currentTimeLabel} sur ${durationLabel}`"
          aria-label="Position de lecture"
          @input="onSeek"
        />
        <div class="d-flex justify-content-between pc-player-times">
          <span>{{ currentTimeLabel }}</span>
          <span>{{ durationLabel }}</span>
        </div>
      </div>

      <!-- Sélecteur de récitateur (choix persisté dans le localStorage) -->
      <div class="pc-player-reciter">
        <label class="visually-hidden" for="pc-reciter-select">Récitateur</label>
        <select
          id="pc-reciter-select"
          class="form-select form-select-sm"
          aria-label="Récitateur"
          :value="player.reciterId"
          @change="onReciterChange"
        >
          <option v-if="!reciterOptions.length" :value="player.reciterId">
            Récitateur {{ player.reciterId }}
          </option>
          <option v-for="r in reciterOptions" :key="r.id" :value="r.id">
            {{ r.name }}{{ r.style && r.style !== r.name ? ` (${r.style})` : '' }}
          </option>
        </select>
      </div>

      <!-- Fermer : stoppe la lecture et masque la barre -->
      <button
        class="btn pc-player-btn pc-player-btn-close"
        type="button"
        aria-label="Fermer le lecteur et arrêter la lecture"
        title="Fermer le lecteur"
        @click="player.stop()"
      >
        <i class="bi bi-x-lg" aria-hidden="true"></i>
      </button>
    </div>

    <!-- Fine ligne de progression dorée en bas de la barre (retour visuel) -->
    <div class="pc-player-track" aria-hidden="true">
      <div class="pc-player-track-fill" :style="{ width: `${progressPercent}%` }"></div>
    </div>
  </aside>
</template>

<style>
/*
 * Style NON scopé : la règle cible <body> pour réserver la place occupée par
 * la barre fixe (le contenu et le footer ne sont plus masqués derrière elle).
 */
body.pc-audio-player-open {
  padding-bottom: 4.5rem;
}
</style>

<style scoped>
/* Barre fixe en bas, vert foncé (texte blanc ≈ 7:1 → AAA), au-dessus de tout */
.pc-audio-player {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  z-index: 1040;
  background-color: var(--pc-green-dark);
  color: #ffffff;
  padding: 0.5rem 0.75rem 0.6rem;
  box-shadow: 0 -2px 10px rgba(0, 0, 0, 0.2);
}

.pc-player-btn {
  color: #ffffff;
  border: 1px solid rgba(255, 255, 255, 0.4);
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.pc-player-btn:hover,
.pc-player-btn:focus {
  color: var(--pc-gold);
  border-color: var(--pc-gold);
}

/* Bouton principal plus grand (cible tactile généreuse) */
.pc-player-btn-main {
  width: 2.7rem;
  height: 2.7rem;
  border-radius: 50%;
  font-size: 1.25rem;
  flex: 0 0 auto;
}

.pc-player-btn-close {
  flex: 0 0 auto;
}

/* Titre : une seule ligne avec ellipsis si trop long */
.pc-player-title {
  max-width: 260px;
}

.pc-player-label {
  display: inline-block;
  max-width: 100%;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-weight: 600;
}

.pc-player-error {
  color: var(--pc-gold);
}

/* Progression : curseur doré sur piste claire translucide */
.pc-player-progress {
  min-width: 140px;
}

.pc-player-range {
  accent-color: var(--pc-gold);
  height: 0.75rem;
  margin: 0;
}

.pc-player-times {
  font-size: 0.75rem;
  color: rgba(255, 255, 255, 0.92);
  font-variant-numeric: tabular-nums;
}

/* Sélecteur de récitateur compact sur fond vert foncé */
.pc-player-reciter {
  max-width: 220px;
}

.pc-player-reciter .form-select {
  background-color: rgba(255, 255, 255, 0.12);
  color: #ffffff;
  border-color: rgba(255, 255, 255, 0.4);
}

.pc-player-reciter .form-select:focus {
  background-color: rgba(255, 255, 255, 0.18);
  color: #ffffff;
}

/* Options du select : fond clair pour rester lisibles (rendu natif navigateur) */
.pc-player-reciter .form-select option {
  color: #212529;
  background-color: #ffffff;
}

/* Ligne de progression dorée en bas de la barre */
.pc-player-track {
  position: absolute;
  left: 0;
  right: 0;
  bottom: 0;
  height: 3px;
  background-color: rgba(255, 255, 255, 0.15);
}

.pc-player-track-fill {
  height: 100%;
  background-color: var(--pc-gold);
  transition: width 0.2s linear;
}

/* Sur mobile : titre pleine largeur sur sa propre ligne (sous les contrôles) */
@media (max-width: 767.98px) {
  .pc-audio-player {
    padding-bottom: 0.75rem;
  }

  .pc-player-title {
    order: 3;
    width: 100%;
    max-width: none;
  }
}
</style>
