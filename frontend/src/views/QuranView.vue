<script setup>
// ===========================================================================
// QuranView (route /quran) : sommaire des 114 sourates.
// ---------------------------------------------------------------------------
// - Chargement de GET /quran/surahs/ au montage ;
// - Recherche locale par nom (translittéré ou arabe) ou par numéro,
//   avec debounce de 200 ms ;
// - Bouton « Reprendre la lecture » pour les utilisateurs connectés dès que
//   GET /quran/progress/ renvoie une position non nulle.
// ===========================================================================
import { ref, computed, onMounted, onBeforeUnmount, watch } from 'vue';
import { getSurahs, getProgress } from '../api/quran';
import { useAuthStore } from '../stores/auth';
import { SURAH_STATUSES, useReadingStatusStore } from '../stores/readingStatus';
import SurahList from '../components/SurahList.vue';
import { useQuranPlayerStore } from '../stores/quranPlayer';

const auth = useAuthStore();
const player = useQuranPlayerStore();
const readingStatus = useReadingStatusStore();
const statusFilter = ref('');

// --- Liste des sourates -----------------------------------------------------
const surahs = ref([]);
const isLoading = ref(false);
const loadError = ref('');

async function loadSurahs() {
  isLoading.value = true;
  loadError.value = '';
  try {
    const { data } = await getSurahs();
    surahs.value = Array.isArray(data) ? data : [];
  } catch {
    loadError.value =
      'Impossible de charger la liste des sourates. Vérifiez votre connexion puis réessayez.';
  } finally {
    isLoading.value = false;
  }
}

// --- Recherche locale (debounce 200 ms) -------------------------------------
const searchInput = ref('');
const debouncedQuery = ref('');
let searchTimer = null;

watch(searchInput, (value) => {
  clearTimeout(searchTimer);
  searchTimer = setTimeout(() => {
    debouncedQuery.value = value.trim();
  }, 200);
});

onBeforeUnmount(() => clearTimeout(searchTimer));

/** Minuscules + suppression des diacritiques pour une recherche tolérante. */
function normalize(text) {
  return String(text || '')
    .toLowerCase()
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '');
}

const filteredSurahs = computed(() => {
  const query = debouncedQuery.value;
  const base = statusFilter.value
    ? surahs.value.filter((s) => readingStatus.statusOf(s.number) === statusFilter.value)
    : surahs.value;
  if (!query) return base;
  const normalized = normalize(query);
  // Recherche par numéro (préfixe) ou par nom (translittéré ou arabe).
  if (/^\d+$/.test(query)) {
    return base.filter((s) => String(s.number).startsWith(query));
  }
  return base.filter(
    (s) =>
      normalize(s.name_transliterated).includes(normalized) ||
      String(s.name_arabic || '').includes(query)
  );
});

// --- Reprendre la lecture (utilisateurs connectés) ---------------------------
const progress = ref(null); // { last_surah_number, last_ayah_number, updated_at }

async function loadProgress() {
  if (!auth.isAuthenticated) return;
  try {
    const { data } = await getProgress();
    progress.value = data;
  } catch {
    // Pas de progression disponible : le bouton ne s'affiche pas, point.
    progress.value = null;
  }
}

const resumeTarget = computed(() => {
  const surah = Number(progress.value?.last_surah_number);
  // Position « non nulle » : numéro de sourate valide (1-114).
  return Number.isInteger(surah) && surah >= 1 && surah <= 114 ? surah : null;
});

const resumeLabel = computed(() => {
  if (!resumeTarget.value) return '';
  const ayah = Number(progress.value?.last_ayah_number);
  return Number.isInteger(ayah) && ayah > 0
    ? `Sourate ${resumeTarget.value}, verset ${ayah}`
    : `Sourate ${resumeTarget.value}`;
});

onMounted(() => {
  loadSurahs();
  loadProgress();
});
</script>

<template>
  <div>
    <!-- En-tête de page -->
    <div class="d-flex flex-wrap align-items-center justify-content-between gap-2 mb-3">
      <div>
        <h1 class="h3 mb-1">Coran</h1>
        <p class="text-muted mb-0">
          Choisissez une sourate pour lire et écouter les versets.
        </p>
      </div>

      <!-- Reprendre la lecture : uniquement si une position existe -->
      <router-link
        v-if="resumeTarget"
        class="btn btn-pc-green"
        :to="{ name: 'surah', params: { number: resumeTarget } }"
      >
        <i class="bi bi-play-fill me-1" aria-hidden="true"></i>
        Reprendre la lecture — {{ resumeLabel }}
      </router-link>
    </div>

    <!-- Recherche (filtrage local, debounce 200 ms) -->
    <div class="mb-3">
      <label class="form-label visually-hidden" for="pc-surah-search">
        Rechercher une sourate
      </label>
      <div class="input-group">
        <span class="input-group-text" aria-hidden="true">
          <i class="bi bi-search"></i>
        </span>
        <input
          id="pc-surah-search"
          v-model="searchInput"
          type="search"
          class="form-control"
          placeholder="Rechercher une sourate (nom ou numéro)…"
          autocomplete="off"
        />
      </div>
      <div class="mt-2">
        <label class="visually-hidden" for="pc-status-filter">Filtrer par statut</label>
        <select id="pc-status-filter" v-model="statusFilter" class="form-select form-select-sm w-auto">
          <option value="">Tous les statuts</option>
          <option v-for="s in SURAH_STATUSES" :key="s.value" :value="s.value">{{ s.label }}</option>
        </select>
      </div>
      <!-- Annonce polie du nombre de résultats (lecteurs d'écran) -->
      <p v-if="debouncedQuery" class="form-text mb-0" aria-live="polite">
        {{ filteredSurahs.length }} sourate{{ filteredSurahs.length > 1 ? 's' : '' }}
        trouvée{{ filteredSurahs.length > 1 ? 's' : '' }} pour « {{ debouncedQuery }} »
      </p>
    </div>

    <!-- États de chargement / erreur -->
    <div v-if="isLoading" class="text-center py-5" role="status">
      <div class="spinner-border pc-spinner" aria-hidden="true"></div>
      <p class="text-muted mt-2 mb-0">Chargement des sourates…</p>
    </div>

    <div v-else-if="loadError" class="alert alert-danger" role="alert">
      {{ loadError }}
      <button class="btn btn-outline-secondary btn-sm ms-2" type="button" @click="loadSurahs">
        Réessayer
      </button>
    </div>

    <div v-else-if="!filteredSurahs.length" class="alert alert-light" role="status">
      Aucune sourate ne correspond à votre recherche ou au statut choisi.
    </div>

    <!-- Liste des sourates -->
    <div v-else class="card shadow-sm">
      <SurahList
        :surahs="filteredSurahs"
        :playing-surah="player.currentSurah"
      />
    </div>
  </div>
</template>

<style scoped>
/* Spinner de chargement aux couleurs de la marque */
.pc-spinner {
  color: var(--pc-green);
}
</style>
