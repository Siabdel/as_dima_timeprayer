<script setup>
// ===========================================================================
// VerseList : liste des versets d'une sourate.
// ---------------------------------------------------------------------------
// - Chaque verset : badge du numéro, texte uthmani en .arabic-text (RTL,
//   grand, interligne généreux), traductions repliables (badges FR / EN) ;
// - Bouton lecture par verset (bi-play) + bouton « Écouter la sourate » en
//   haut de liste (lecture/pause du chapitre entier) ;
// - Le verset en cours de lecture est surligné (fond or pâle + bordure
//   gauche verte) quand la lecture active correspond ;
// - Progression : si l'utilisateur est connecté, PUT /quran/progress/ à
//   chaque verset consulté (debounce 2 s, non bloquant).
// ===========================================================================
import { reactive, watch, nextTick, onBeforeUnmount } from 'vue';
import { useQuranPlayerStore } from '../stores/quranPlayer';
import { useAuthStore } from '../stores/auth';
import { updateProgress } from '../api/quran';
import WordByWordReader from './WordByWordReader.vue';

const props = defineProps({
  /** Versets de la sourate (réponse de GET /quran/surahs/{n}/). */
  verses: { type: Array, default: () => [] },
  /** Numéro de la sourate affichée. */
  surah: { type: Number, required: true },
  /** Bascule GLOBALE des traductions (checkbox FR / EN de la page). */
  showTranslations: { type: Boolean, default: true },
  /** Affiche la translittération phonétique sous le texte arabe. */
  showPhonetic: { type: Boolean, default: false },
  /** Mode « mot à mot » : rend WordByWordReader quand le verset a `words`. */
  wordByWord: { type: Boolean, default: false },
  /** Index du mot en cours par verset : { [ayahNumber]: index }. */
  activeWordIndex: { type: Object, default: () => ({}) },
  /** Verset en cours de récitation (suivi verset/mot), null si aucun. */
  followAyah: { type: Number, default: null },
});

const emit = defineEmits(['play-verse', 'word-click', 'active-word']);

const player = useQuranPlayerStore();
const auth = useAuthStore();

// --- Traductions : repli global (prop) + repli individuel par verset -------
// localOpen[ayah] mémorise le choix manuel ; absent = déplié par défaut.
const localOpen = reactive({});

function hasTranslations(verse) {
  return Array.isArray(verse.translations) && verse.translations.length > 0;
}

/** Traductions visibles pour un verset (global OFF → toujours replié). */
function translationsOpen(ayah) {
  if (!props.showTranslations) return false;
  return localOpen[ayah] ?? true;
}

function toggleTranslations(ayah) {
  localOpen[ayah] = !translationsOpen(ayah);
}

/** Libellé court du code de traduction : « french » → badge « FR ». */
function codeLabel(code) {
  const map = { french: 'FR', english: 'EN', fr: 'FR', en: 'EN' };
  const key = String(code || '').toLowerCase();
  return map[key] ?? String(code || '??').slice(0, 2).toUpperCase();
}

/** Phonétique du verset : translittération des mots (marqueur de fin exclu). */
function phonetic(verse) {
  if (!Array.isArray(verse.words)) return '';
  return verse.words
    .filter((w) => !w.is_end && w.transliteration)
    .map((w) => w.transliteration)
    .join(' ');
}

// --- Mode « mot à mot » ------------------------------------------------------

/** Vrai si CE verset doit être rendu en mode mot à mot. */
function usesWordByWord(verse) {
  return props.wordByWord && Array.isArray(verse.words) && verse.words.length > 0;
}

/** Index du mot actif pour ce verset (-1 si aucun mot en cours). */
function wordIndexFor(verse) {
  const index = props.activeWordIndex?.[verse.ayah_number];
  return Number.isInteger(index) ? index : -1;
}

/** Clic sur un mot (WordByWordReader) → remonté à la page, avec le mot. */
function onWordClick(verse, index) {
  const word = verse.words?.[index] ?? null;
  emit('word-click', { ayah: verse.ayah_number, index, word });
}

/**
 * Mot en cours annoncé par le lecteur mot à mot → remonté à la page, qui
 * détient l'unique région aria-live (évite une région par verset).
 */
function onActiveWord(label) {
  emit('active-word', label);
}

// --- Lecture ---------------------------------------------------------------

/** Clic « lire ce verset » : émission vers la page + suivi de progression. */
function onPlayVerse(verse) {
  emit('play-verse', verse);
  scheduleProgressSync(props.surah, verse.ayah_number);
}

/** Bouton du haut : lecture / pause de la sourate entière. */
function onPlaySurah() {
  player.playSurah(props.surah);
}

/** Vrai si CE verset est celui suivi pendant la récitation de la sourate. */
function isFollowedVerse(verse) {
  return props.followAyah !== null && props.followAyah === verse.ayah_number;
}

/** Vrai si CE verset est la source actuellement chargée dans le lecteur. */
function isActiveVerse(verse) {
  if (isFollowedVerse(verse)) return true;
  return (
    player.currentSurah === props.surah &&
    player.currentAyah === verse.ayah_number &&
    player.audioUrl !== null
  );
}

/** Vrai si la lecture active (non en pause) porte sur CE verset. */
function isPlayingVerse(verse) {
  return isActiveVerse(verse) && player.playing;
}

/** Icône du bouton par verset : pause si c'est le verset en cours. */
function versePlayIcon(verse) {
  return isPlayingVerse(verse) ? 'bi-pause-fill' : 'bi-play-fill';
}

/** Le bouton du haut montre « Pause » quand le chapitre joue. */
const surahIsPlaying = () =>
  player.currentSurah === props.surah &&
  player.currentAyah === null &&
  player.playing;

// --- Progression (utilisateurs connectés) : debounce 2 s, non bloquant ------

let progressTimer = null;

function scheduleProgressSync(surah, ayah) {
  if (!auth.isAuthenticated) return;
  if (progressTimer) clearTimeout(progressTimer);
  progressTimer = setTimeout(() => {
    progressTimer = null;
    // Non bloquant : une erreur réseau ne doit jamais gêner la lecture.
    updateProgress({ last_surah_number: surah, last_ayah_number: ayah }).catch(
      () => {}
    );
  }, 2000);
}

// Verset consulté aussi quand la lecture avance via le lecteur persistant
// (ex. démarrée depuis la page d'accueil puis rejointe ici).
watch(
  () => [player.currentSurah, player.currentAyah, player.audioUrl],
  ([surah, ayah, url]) => {
    if (url && surah === props.surah && ayah !== null) {
      scheduleProgressSync(props.surah, ayah);
    }
  }
);

// Défilement automatique vers le verset récité (centré, doux ; instantané si
// l'utilisateur préfère réduire les animations).
watch(
  () => props.followAyah,
  async (ayah) => {
    if (ayah === null) return;
    await nextTick();
    const el = document.getElementById(`verse-${props.surah}-${ayah}`);
    if (!el || typeof el.scrollIntoView !== 'function') return;
    const reduce = window.matchMedia?.('(prefers-reduced-motion: reduce)')?.matches;
    el.scrollIntoView({ block: 'center', behavior: reduce ? 'auto' : 'smooth' });
  }
);

onBeforeUnmount(() => {
  if (progressTimer) clearTimeout(progressTimer);
});
</script>

<template>
  <div>
    <!-- Barre du haut : lecture / pause de la sourate entière -->
    <div class="d-flex align-items-center mb-3">
      <button
        class="btn btn-pc-green"
        type="button"
        :aria-label="surahIsPlaying() ? `Mettre en pause la sourate ${surah}` : `Écouter la sourate ${surah}`"
        @click="onPlaySurah"
      >
        <span
          v-if="player.loading"
          class="spinner-border spinner-border-sm me-1"
          role="status"
          aria-hidden="true"
        ></span>
        <i
          v-else
          class="bi me-1"
          :class="surahIsPlaying() ? 'bi-pause-fill' : 'bi-play-fill'"
          aria-hidden="true"
        ></i>
        {{ surahIsPlaying() ? 'Pause' : 'Écouter la sourate' }}
      </button>
    </div>

    <!-- Versets -->
    <ol class="list-unstyled mb-0 pc-verse-list">
      <li
        v-for="verse in verses"
        :id="`verse-${surah}-${verse.ayah_number}`"
        :key="verse.ayah_number"
        class="card mb-3 pc-verse-card"
        :class="{
          'pc-verse-active': isActiveVerse(verse),
          'pc-verse-following': isFollowedVerse(verse),
        }"
        :aria-current="isFollowedVerse(verse) ? 'true' : undefined"
      >
        <div class="card-body py-3">
          <div class="d-flex align-items-start gap-3">
            <div class="d-flex flex-column align-items-center gap-2 pc-verse-side">
              <span
                class="badge pc-verse-badge"
                :aria-label="`Verset ${verse.ayah_number}`"
              >
                {{ verse.ayah_number }}
              </span>
              <button
                class="btn btn-sm btn-pc-green pc-verse-play"
                type="button"
                :aria-label="
                  isPlayingVerse(verse)
                    ? `Mettre en pause le verset ${verse.ayah_number}`
                    : `Lire le verset ${verse.ayah_number}`
                "
                @click="onPlayVerse(verse)"
              >
                <i class="bi" :class="versePlayIcon(verse)" aria-hidden="true"></i>
              </button>
            </div>

            <div class="flex-grow-1 min-w-0">
              <!-- Mode « mot à mot » : un mot illuminé à la fois + sa traduction -->
              <WordByWordReader
                v-if="usesWordByWord(verse)"
                class="mb-2"
                :words="verse.words"
                :active-index="wordIndexFor(verse)"
                :playing="player.playing"
                @word-click="onWordClick(verse, $event)"
                @active-word="onActiveWord"
              />

              <!-- Mode normal : texte uthmani complet (Amiri, RTL, aéré) -->
              <p v-else class="arabic-text pc-verse-arabic mb-2" lang="ar" dir="rtl">
                {{ verse.text_uthmani }}
              </p>

              <!-- Phonétique (translittération latine) -->
              <p
                v-if="showPhonetic && phonetic(verse)"
                class="pc-phonetic fst-italic mb-2"
                lang="ar-Latn"
              >
                <span class="badge pc-translation-badge me-1" aria-hidden="true">PH</span>
                {{ phonetic(verse) }}
              </p>

              <!-- Traductions repliables (badges FR / EN) -->
              <div
                v-if="translationsOpen(verse.ayah_number) && hasTranslations(verse)"
                :id="`verse-${surah}-${verse.ayah_number}-translations`"
                class="pc-translations"
              >
                <p
                  v-for="(t, index) in verse.translations"
                  :key="`${t.resource_id}-${index}`"
                  class="pc-translation mb-1"
                >
                  <span class="badge pc-translation-badge" aria-hidden="true">
                    {{ codeLabel(t.code) }}
                  </span>
                  <span class="pc-translation-text">{{ t.text }}</span>
                </p>
              </div>
            </div>
          </div>

          <!-- Bascule individuelle des traductions (repli/dépli par verset) -->
          <div
            v-if="showTranslations && hasTranslations(verse)"
            class="text-end mt-1"
          >
            <button
              class="btn btn-sm pc-fold-btn"
              type="button"
              :aria-expanded="translationsOpen(verse.ayah_number)"
              :aria-controls="`verse-${surah}-${verse.ayah_number}-translations`"
              @click="toggleTranslations(verse.ayah_number)"
            >
              <i
                class="bi me-1"
                :class="
                  translationsOpen(verse.ayah_number)
                    ? 'bi-chevron-up'
                    : 'bi-chevron-down'
                "
                aria-hidden="true"
              ></i>
              {{
                translationsOpen(verse.ayah_number)
                  ? 'Masquer la traduction'
                  : 'Afficher la traduction'
              }}
            </button>
          </div>
        </div>
      </li>
    </ol>
  </div>
</template>

<style scoped>
/* Verset en cours de lecture : fond or pâle + bordure gauche verte */
.pc-verse-active {
  background-color: rgba(233, 196, 106, 0.25);
  border-left: 4px solid var(--pc-green);
}

.pc-verse-card {
  border-radius: 0.75rem;
  transition: background-color 0.2s ease, box-shadow 0.2s ease;
  scroll-margin-block: 5rem;
}

/* Verset suivi pendant la récitation : encadré net (en plus du fond or) */
.pc-verse-following {
  box-shadow: 0 0 0 2px var(--pc-green);
}

@media (prefers-reduced-motion: reduce) {
  .pc-verse-card {
    transition: none;
  }
}

/* Colonne latérale : badge numéro + bouton lecture */
.pc-verse-side {
  flex: 0 0 auto;
  padding-top: 0.25rem;
}

/* Badge du numéro : rond, vert de marque (texte blanc AA) */
.pc-verse-badge {
  width: 2rem;
  height: 2rem;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  background-color: var(--pc-green);
  color: #ffffff;
  font-weight: 600;
  font-variant-numeric: tabular-nums;
}

.pc-verse-play {
  border-radius: 50%;
  width: 2.2rem;
  height: 2.2rem;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 0;
}

/* Texte arabe du verset : plus grand que la classe de base, interligne généreux */
.pc-verse-arabic {
  font-size: 1.7rem;
  line-height: 2.2;
  text-align: right;
  word-break: break-word;
}

/* Traductions : gris-vert lisible, badge du code en vert */
.pc-translations {
  border-top: 1px dashed rgba(20, 116, 111, 0.2);
  padding-top: 0.5rem;
  margin-top: 0.25rem;
}

.pc-translation {
  color: #3f4b4a;
  line-height: 1.6;
}

.pc-translation-badge {
  background-color: var(--pc-green);
  color: #ffffff;
  font-weight: 600;
  margin-inline-end: 0.4rem;
}

/* Bouton de repli discret mais contrasté (or assombri AA sur blanc) */
.pc-fold-btn {
  color: var(--pc-green);
  font-size: 0.85rem;
}

.pc-fold-btn:hover {
  color: var(--pc-green-dark);
}

.min-w-0 {
  min-width: 0;
}
.pc-phonetic {
  color: #3f4b4a;
  line-height: 1.7;
}
</style>
