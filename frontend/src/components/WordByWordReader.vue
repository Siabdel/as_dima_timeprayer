<script setup>
// ===========================================================================
// WordByWordReader : lecture « mot à mot » d'UN verset.
// ---------------------------------------------------------------------------
// - Les mots arabes sont affichés en ligne, RTL, en .arabic-text (Amiri) ;
// - Sous CHAQUE mot : sa traduction française (translation_fr), petite et
//   centrée ; le marqueur de fin de verset (is_end) est rendu en numéro dans
//   un cercle, sans traduction dessous (il n'est jamais surligné ni joué) ;
// - Le mot actif (activeIndex) est illuminé : fond ambre/or, bordure basse
//   verte, léger scale, transition CSS fluide (0.15 s) ;
// - Accessibilité : chaque mot est un <span role="button" tabindex="0"> avec
//   un aria-label complet (« mot arabe — traduction »), et le mot en cours est
//   annoncé via UNE SEULE région aria-live="polite" ;
// - Émet 'word-click' (index) : le parent peut rejouer à partir de ce mot.
// ===========================================================================
import { computed, watch } from 'vue';

const props = defineProps({
  /** Mots du verset (réponse de GET /quran/surahs/{n}/?words=true). */
  words: { type: Array, default: () => [] },
  /** Index du mot en cours de lecture, ou -1 si aucun. */
  activeIndex: { type: Number, default: -1 },
  /** Vrai pendant la lecture mot à mot (indicateur visuel + aria-busy). */
  playing: { type: Boolean, default: false },
});

const emit = defineEmits(['word-click', 'active-word']);

/** Mot actif (null si l'index est hors bornes). */
const activeWord = computed(() => {
  const index = props.activeIndex;
  if (!Number.isInteger(index) || index < 0 || index >= props.words.length) {
    return null;
  }
  return props.words[index];
});

/**
 * Texte du mot en cours : « mot arabe — traduction ».
 * Remonté au parent, qui possède LA SEULE région aria-live="polite" de la page
 * (une région par verset ferait bégayer les lecteurs d'écran).
 */
const activeLabel = computed(() => {
  const word = activeWord.value;
  if (!word) return '';
  const translation = word.translation_fr || word.translation_en || '';
  return translation ? `${word.text_uthmani} — ${translation}` : word.text_uthmani;
});

// Annonce le mot en cours au parent à chaque changement (pas de spam : une
// seule émission par changement réel de mot).
watch(activeLabel, (label) => {
  if (label) emit('active-word', label);
});

/** Vrai si le mot est le marqueur de fin de verset (jamais surligné/joué). */
function isEndMarker(word) {
  return word?.is_end === true;
}

/** Vrai si CE mot est celui en cours de lecture. */
function isActive(index, word) {
  return index === props.activeIndex && !isEndMarker(word);
}

/** Traduction affichée sous le mot (français, repli anglais). */
function translationOf(word) {
  return word?.translation_fr || word?.translation_en || '';
}

/** aria-label complet : « mot arabe — traduction ». */
function wordLabel(word) {
  const parts = [word?.text_uthmani || ''];
  const translation = translationOf(word);
  if (translation) parts.push(translation);
  if (word?.transliteration) parts.push(word.transliteration);
  return parts.filter(Boolean).join(' — ');
}

/** Clic (ou Entrée / Espace) sur un mot : rejoue à partir de cette position. */
function onWordClick(index, word) {
  if (isEndMarker(word)) return;
  emit('word-click', index);
}
</script>

<template>
  <div class="pc-wbw" :aria-busy="playing ? 'true' : 'false'">
    <!-- Mots arabes en ligne, RTL -->
    <div class="pc-wbw-words" dir="rtl" lang="ar">
      <template v-for="(word, index) in words" :key="`${index}-${word.position}`">
        <!-- Marqueur de fin de verset : numéro en cercle, sans traduction -->
        <span
          v-if="isEndMarker(word)"
          class="pc-wbw-end"
          aria-hidden="true"
        >
          <span class="pc-wbw-end-badge">{{ word.text_uthmani }}</span>
        </span>

        <!-- Mot normal : arabe + traduction française dessous -->
        <span
          v-else
          class="pc-wbw-cell"
          :class="{ 'pc-wbw-active': isActive(index, word) }"
          role="button"
          tabindex="0"
          :aria-label="wordLabel(word)"
          :aria-current="isActive(index, word) ? 'true' : undefined"
          @click="onWordClick(index, word)"
          @keydown.enter.prevent="onWordClick(index, word)"
          @keydown.space.prevent="onWordClick(index, word)"
        >
          <span class="arabic-text pc-wbw-arabic">{{ word.text_uthmani }}</span>
          <span class="pc-wbw-translation" dir="ltr" lang="fr">
            {{ translationOf(word) }}
          </span>
        </span>
      </template>
    </div>
  </div>
</template>

<style scoped>
/* Conteneur : fond très légèrement teinté pour détacher le mode mot à mot */
.pc-wbw {
  padding: 0.5rem 0.25rem;
  border-radius: 0.5rem;
  background-color: rgba(20, 116, 111, 0.04);
}

/* Ligne des mots : RTL, retour à la ligne naturel, gouttières régulières */
.pc-wbw-words {
  display: flex;
  flex-wrap: wrap;
  align-items: flex-end;
  justify-content: flex-start;
  gap: 0.4rem 0.55rem;
}

/* Une cellule = un mot arabe + sa traduction française dessous */
.pc-wbw-cell {
  display: inline-flex;
  flex-direction: column;
  align-items: center;
  min-width: 3.2rem;
  padding: 0.1rem 0.35rem 0.2rem;
  border-radius: 0.4rem;
  border-bottom: 2px solid transparent;
  cursor: pointer;
  transform: scale(1);
  transition: background-color 0.15s ease, border-color 0.15s ease,
    transform 0.15s ease, box-shadow 0.15s ease;
}

.pc-wbw-cell:hover {
  background-color: rgba(233, 196, 106, 0.18);
}

.pc-wbw-cell:focus-visible {
  outline: 3px solid var(--pc-gold-dark);
  outline-offset: 2px;
}

/* Mot en cours de lecture : ambre/or + bordure basse verte + léger scale */
.pc-wbw-active {
  background-color: rgba(233, 196, 106, 0.35);
  border-bottom-color: var(--pc-green);
  transform: scale(1.06);
  box-shadow: 0 2px 6px rgba(138, 109, 31, 0.25);
}

/* Mot arabe : grand, aéré (classe .arabic-text = police Amiri + RTL) */
.pc-wbw-arabic {
  font-size: 1.85rem;
  line-height: 1.9;
  white-space: nowrap;
}

/* Traduction française sous le mot : petite, grise, centrée */
.pc-wbw-translation {
  font-size: 0.72rem;
  line-height: 1.25;
  color: #6c757d;
  text-align: center;
  max-width: 8.5rem;
  direction: ltr;
}

/* Mot actif : traduction plus contrastée (lisibilité pendant la lecture) */
.pc-wbw-active .pc-wbw-translation {
  color: #3f4b4a;
  font-weight: 600;
}

/* Marqueur de fin de verset : numéro dans un cercle vert */
.pc-wbw-end {
  display: inline-flex;
  align-items: center;
  align-self: center;
  padding: 0 0.15rem;
}

.pc-wbw-end-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 2rem;
  height: 2rem;
  padding: 0 0.3rem;
  border-radius: 50%;
  border: 1px solid var(--pc-green);
  background-color: rgba(20, 116, 111, 0.08);
  color: var(--pc-green-dark);
  font-weight: 600;
  font-size: 0.95rem;
  font-variant-numeric: tabular-nums;
}

/* Mouvement réduit : on garde la couleur, on supprime le scale */
@media (prefers-reduced-motion: reduce) {
  .pc-wbw-cell {
    transition: none;
  }

  .pc-wbw-active {
    transform: none;
  }
}
</style>
