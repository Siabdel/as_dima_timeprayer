<script setup>
// ===========================================================================
// SurahView (route /quran/:number) : lecture d'une sourate.
// ---------------------------------------------------------------------------
// - En-tête : nom arabe (Amiri RTL), nom translittéré, nombre de versets,
//   bouton retour vers la liste ;
// - Sélecteur de traductions (checkbox FR / EN, FR cochée par défaut) ;
// - VerseList : les boutons « lire le verset » lancent playVerse() du store
//   persistant ; le lecteur AudioPlayer (dans App.vue) reste visible.
// ===========================================================================
import { ref, computed, watch, onMounted } from 'vue';
import { useRoute } from 'vue-router';
import { getSurahs, getVerses } from '../api/quran';
import { useQuranPlayerStore } from '../stores/quranPlayer';
import { usePreferencesStore } from '../stores/preferences';
import VerseList from '../components/VerseList.vue';

const route = useRoute();
const player = useQuranPlayerStore();

// --- Paramètre de route : numéro de sourate (1-114) --------------------------
const surahNumber = computed(() => {
  const n = Number.parseInt(route.params.number, 10);
  return Number.isInteger(n) && n >= 1 && n <= 114 ? n : null;
});

// --- Métadonnées de la sourate ------------------------------------------------
// Cache module-level : évite de recharger les 114 entrées à chaque navigation.
let surahsCache = null;

const surahMeta = ref(null); // { name_arabic, name_transliterated, ... }

async function loadSurahMeta() {
  surahMeta.value = null;
  if (surahNumber.value === null) return;
  try {
    if (!surahsCache) {
      const { data } = await getSurahs();
      surahsCache = Array.isArray(data) ? data : [];
    }
    surahMeta.value =
      surahsCache.find((s) => s.number === surahNumber.value) ?? null;
  } catch {
    // Métadonnées indisponibles : la page reste utilisable (versets + lecteur).
    surahMeta.value = null;
  }
}

// --- Versets + traductions sélectionnées --------------------------------------
const translationsOptions = [
  { code: 'fr', label: 'Français (FR)' },
  { code: 'en', label: 'Anglais (EN)' },
];
// Traduction par défaut : langue choisie dans les Réglages (FR sinon).
const selectedTranslations = ref([
  usePreferencesStore().preference?.language === 'en' ? 'en' : 'fr',
]);

// Affichage : traduction et phonétique masquables indépendamment (persisté).
function readFlag(key, fallback) {
  try {
    const raw = window.localStorage.getItem(key);
    return raw === null ? fallback : raw === '1';
  } catch {
    return fallback;
  }
}
const showTranslation = ref(readFlag('pc_show_translation', true));
const showPhonetic = ref(readFlag('pc_show_phonetic', true));
watch([showTranslation, showPhonetic], () => {
  try {
    window.localStorage.setItem('pc_show_translation', showTranslation.value ? '1' : '0');
    window.localStorage.setItem('pc_show_phonetic', showPhonetic.value ? '1' : '0');
  } catch {
    // Stockage indisponible : sans conséquence.
  }
});

const verses = ref([]);
const isLoading = ref(false);
const loadError = ref('');

// --- Mode « mot à mot » -------------------------------------------------------
// Le switch est adossé au store (persisté dans le localStorage « pc_word_mode ») :
// l'état survit donc à la navigation et au rechargement de la page.
// Suivi de la récitation (verset / mot), adossé au store (persisté).
const followModes = [
  { value: 'off', label: 'Désactivé' },
  { value: 'ayah', label: 'Verset par verset' },
  { value: 'word', label: 'Mot par mot' },
];
const followMode = computed({
  get: () => player.followMode,
  set: (value) => player.setFollowMode(value),
});

/** Le suivi mot par mot a besoin du tableau `words` pour rendre les mots. */
const showWords = computed(() => wordByWord.value || followMode.value === 'word');

/** La phonétique est reconstruite à partir des mots (`words=true`). */
const needWords = computed(() => showWords.value || showPhonetic.value);

/** Mot actif transmis à VerseList : séquence mot à mot OU suivi de récitation. */
const activeWords = computed(() => {
  if (followMode.value === 'word' && player.followAyah !== null && player.followWordIndex >= 0) {
    return { [player.followAyah]: player.followWordIndex };
  }
  return player.activeWordIndex;
});

/** Verset suivi (null hors suivi ou hors lecture de la sourate entière). */
const followedAyah = computed(() =>
  followMode.value !== 'off' && player.currentSurah === surahNumber.value
    ? player.followAyah
    : null
);

const wordByWord = computed({
  get: () => player.wordByWordMode,
  set: (value) => player.setWordByWordMode(value),
});

async function loadVerses() {
  if (surahNumber.value === null) {
    loadError.value =
      'Numéro de sourate invalide. Choisissez une sourate entre 1 et 114.';
    verses.value = [];
    return;
  }
  isLoading.value = true;
  loadError.value = '';
  verses.value = [];
  try {
    // En mode mot à mot, `words=true` fait renvoyer le tableau `words` par
    // verset (mots isolés + traduction française + audio dédié).
    const { data } = await getVerses(
      surahNumber.value,
      selectedTranslations.value,
      { words: needWords.value }
    );
    verses.value = Array.isArray(data) ? data : [];
  } catch {
    loadError.value =
      "Impossible de charger les versets de cette sourate. Vérifiez votre connexion puis réessayez.";
  } finally {
    isLoading.value = false;
  }
}

// Traductions cochées → rechargement des versets (requête légère, publique).
watch(selectedTranslations, loadVerses, { deep: true });

// Bascule du mode mot à mot → refetch avec (ou sans) `words=true`.
watch(needWords, loadVerses);

// Navigation sourate → sourate (retour puis nouvelle sourate) : rechargement.
watch(
  () => route.params.number,
  () => {
    // La séquence de mots ne doit pas survivre à un changement de sourate.
    player.stopWordsSequence();
    loadSurahMeta();
    loadVerses();
  }
);

/** Lecture d'un verset : émis par VerseList, délégué au store persistant. */
function onPlayVerse(verse) {
  player.playVerse(surahNumber.value, verse.ayah_number);
}

// --- Lecture mot à mot --------------------------------------------------------

/** Vrai quand la séquence mot à mot est en cours. */
const wordsSequencePlaying = computed(() => player.isWordSequencePlaying);

/** Versets effectivement porteurs du tableau `words` (mode mot à mot actif). */
const versesWithWords = computed(() =>
  verses.value.filter((v) => Array.isArray(v.words) && v.words.length > 0)
);

/**
 * Démarre la lecture mot à mot des versets affichés.
 * Si la lecture normale était en cours, elle est mise en pause par le store.
 */
function onPlayWords() {
  player.playWordsSequence(versesWithWords.value, 0, surahNumber.value);
}

/** Arrête la séquence mot à mot (le lecteur de sourate n'est pas touché). */
function onStopWords() {
  player.stopWordsSequence();
  activeWordLabel.value = '';
}

/** Clic sur un mot : reprend la séquence À PARTIR de ce mot. */
function onWordClick({ ayah, index }) {
  // Suivi seul (sans séquence mot à mot) : saute à ce mot dans la récitation.
  if (!wordByWord.value && player.seekToWord(ayah, index)) return;
  player.playWordsFrom(versesWithWords.value, ayah, index, surahNumber.value);
}

/**
 * Mot en cours annoncé par WordByWordReader. LA SEULE région aria-live de la
 * page : une région par verset ferait bégayer les lecteurs d'écran.
 */
const activeWordLabel = ref('');

function onActiveWord(label) {
  activeWordLabel.value = label;
}

/** Libellé du lieu de révélation pour l'en-tête. */
function revelationLabel(place) {
  switch (String(place || '').toLowerCase()) {
    case 'makkah':
    case 'mecca':
      return 'La Mecque';
    case 'madinah':
    case 'medina':
      return 'Médine';
    default:
      return '';
  }
}

onMounted(() => {
  loadSurahMeta();
  loadVerses();
});
</script>

<template>
  <div>
    <!-- Retour vers la liste des sourates -->
    <router-link class="btn btn-outline-secondary btn-sm mb-3" :to="{ name: 'quran' }">
      <i class="bi bi-arrow-left me-1" aria-hidden="true"></i>
      Toutes les sourates
    </router-link>

    <!-- Numéro invalide -->
    <div v-if="surahNumber === null" class="alert alert-warning" role="alert">
      Numéro de sourate invalide. Choisissez une sourate entre 1 et 114.
    </div>

    <template v-else>
      <!-- En-tête de la sourate -->
      <header
        v-if="surahMeta"
        class="card shadow-sm mb-3 pc-surah-header"
        aria-label="Informations sur la sourate"
      >
        <div class="card-body d-flex flex-wrap align-items-center gap-3">
          <span class="pc-surah-badge" aria-hidden="true">{{ surahMeta.number }}</span>
          <div class="flex-grow-1">
            <h1 class="h3 mb-0">{{ surahMeta.name_transliterated }}</h1>
            <p class="text-muted mb-0">
              {{ surahMeta.verses_count }} verset{{ surahMeta.verses_count > 1 ? 's' : '' }}
              <template v-if="revelationLabel(surahMeta.revelation_place)">
                · {{ revelationLabel(surahMeta.revelation_place) }}
              </template>
            </p>
          </div>
          <span class="arabic-text pc-surah-header-arabic" lang="ar" dir="rtl">
            {{ surahMeta.name_arabic }}
          </span>
        </div>
      </header>

      <!-- Sélecteur de traductions (FR cochée par défaut) + mode mot à mot -->
      <fieldset class="mb-3">
        <legend class="form-label mb-1 pc-legend">Traductions affichées</legend>
        <div class="d-flex flex-wrap align-items-center gap-3">
          <div
            v-for="option in translationsOptions"
            :key="option.code"
            class="form-check"
          >
            <input
              :id="`pc-tr-${option.code}`"
              v-model="selectedTranslations"
              class="form-check-input"
              type="checkbox"
              :value="option.code"
            />
            <label class="form-check-label" :for="`pc-tr-${option.code}`">
              {{ option.label }}
            </label>
          </div>

          <!-- Suivi de la récitation : verset encadré / mot illuminé -->
          <div
            class="btn-group pc-follow-group"
            role="radiogroup"
            aria-label="Suivi de la récitation"
          >
            <template v-for="m in followModes" :key="m.value">
              <input
                :id="`pc-follow-${m.value}`"
                v-model="followMode"
                class="btn-check"
                type="radio"
                name="pc-follow-mode"
                :value="m.value"
              />
              <label class="btn btn-sm btn-outline-secondary" :for="`pc-follow-${m.value}`">
                {{ m.label }}
              </label>
            </template>
          </div>

          <!-- Lecture mot à mot : chaque mot illuminé au rythme de la récitation -->
          <div class="form-check form-switch pc-word-switch">
            <input
              id="pc-word-mode"
              v-model="wordByWord"
              class="form-check-input"
              type="checkbox"
              role="switch"
              aria-describedby="pc-word-mode-help"
            />
            <label class="form-check-label" for="pc-word-mode">
              Lecture mot à mot
            </label>
          </div>
        </div>
        <div class="d-flex flex-wrap gap-3 mt-2">
          <div class="form-check form-switch">
            <input id="pc-show-translation" v-model="showTranslation" class="form-check-input" type="checkbox" role="switch" />
            <label class="form-check-label" for="pc-show-translation">Traduction</label>
          </div>
          <div class="form-check form-switch">
            <input id="pc-show-phonetic" v-model="showPhonetic" class="form-check-input" type="checkbox" role="switch" />
            <label class="form-check-label" for="pc-show-phonetic">Phonétique (pour ne pas lire l'arabe)</label>
          </div>
        </div>
        <p class="form-text mb-1">
          <strong>Suivi de la récitation</strong> : pendant « Écouter la sourate »,
          le verset (ou le mot) récité est surligné et la page défile
          automatiquement.
        </p>
        <p id="pc-word-mode-help" class="form-text mb-0">
          Chaque mot arabe est illuminé au rythme de la récitation, avec sa
          traduction française juste en dessous.
        </p>
      </fieldset>

      <!-- Commandes de la séquence mot à mot (mode actif uniquement) -->
      <div
        v-if="wordByWord && !isLoading && !loadError"
        class="d-flex flex-wrap align-items-center gap-2 mb-3 pc-word-controls"
      >
        <button
          class="btn btn-pc-green"
          type="button"
          :disabled="!versesWithWords.length"
          @click="onPlayWords"
        >
          <i class="bi bi-play-circle me-1" aria-hidden="true"></i>
          Écouter mot à mot
        </button>
        <button
          v-if="wordsSequencePlaying"
          class="btn btn-outline-secondary"
          type="button"
          @click="onStopWords"
        >
          <i class="bi bi-stop-fill me-1" aria-hidden="true"></i>
          Arrêter
        </button>
        <!-- Statut visuel uniquement : l'annonce aux lecteurs d'écran est
             assurée par LA SEULE région aria-live de la page (plus bas).
             Une seconde région aria-live ici ferait annoncer chaque mot deux fois. -->
        <span class="text-muted pc-word-status" aria-hidden="true">
          {{ wordsSequencePlaying ? player.wordSequenceLabel : '' }}
        </span>
      </div>

      <!-- États de chargement / erreur -->
      <div v-if="isLoading" class="text-center py-5" role="status">
        <div class="spinner-border pc-spinner" aria-hidden="true"></div>
        <p class="text-muted mt-2 mb-0">Chargement des versets…</p>
      </div>

      <div v-else-if="loadError" class="alert alert-danger" role="alert">
        {{ loadError }}
        <button class="btn btn-outline-secondary btn-sm ms-2" type="button" @click="loadVerses">
          Réessayer
        </button>
      </div>

      <!-- Versets : le lecteur persistant (App.vue) reste visible en bas -->
      <VerseList
        v-else
        :verses="verses"
        :surah="surahNumber"
        :show-translations="showTranslation && selectedTranslations.length > 0"
        :show-phonetic="showPhonetic"
        :word-by-word="showWords"
        :active-word-index="activeWords"
        :follow-ayah="followedAyah"
        @play-verse="onPlayVerse"
        @word-click="onWordClick"
        @active-word="onActiveWord"
      />

      <!-- SEULE région aria-live de la page : annonce le mot en cours -->
      <p class="visually-hidden" aria-live="polite">{{ activeWordLabel }}</p>
    </template>
  </div>
</template>

<style scoped>
/* En-tête de sourate : léger rappel de marque */
.pc-surah-header {
  border-left: 4px solid var(--pc-green);
}

.pc-surah-header-arabic {
  font-size: 1.8rem;
  line-height: 1.8;
}

/* Badge rond vert (même style que la liste) */
.pc-surah-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 2.8rem;
  height: 2.8rem;
  border-radius: 50%;
  background-color: var(--pc-green);
  color: #ffffff;
  font-weight: 600;
  flex: 0 0 auto;
}

/* Legend du fieldset sans le style de titre par défaut */
.pc-legend {
  font-size: 0.95rem;
  color: #3f4b4a;
}

/* Switch « Lecture mot à mot » : accentué vert de marque */
.pc-word-switch .form-check-input {
  cursor: pointer;
}

.pc-word-switch .form-check-input:checked {
  background-color: var(--pc-green);
  border-color: var(--pc-green);
}

.pc-word-switch .form-check-input:focus {
  border-color: var(--pc-green);
  box-shadow: 0 0 0 0.2rem rgba(20, 116, 111, 0.25);
}

.pc-word-switch .form-check-label {
  cursor: pointer;
}

/* Bandeau des commandes mot à mot */
.pc-word-controls {
  padding: 0.6rem 0.75rem;
  border-radius: 0.5rem;
  border-left: 4px solid var(--pc-gold);
  background-color: rgba(233, 196, 106, 0.12);
}

.pc-word-status {
  font-size: 0.9rem;
  font-variant-numeric: tabular-nums;
}

.pc-follow-group .btn-check:checked + .btn {
  background-color: var(--pc-green);
  border-color: var(--pc-green);
  color: #ffffff;
}

.pc-spinner {
  color: var(--pc-green);
}
</style>
