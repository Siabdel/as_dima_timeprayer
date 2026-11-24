<script setup>
// ===========================================================================
// CountdownTimer : compte à rebours avant la prochaine prière.
// ---------------------------------------------------------------------------
// - Compare l'heure courante à l'heure ACTUELLE DU LIEU (via la timezone
//   renvoyée par l'API, avec Intl.DateTimeFormat) ;
// - Mise à jour chaque seconde (setInterval, nettoyé dans onBeforeUnmount) ;
// - Émet « next-prayer » (nom de la prochaine prière) pour que la grille
//   de cartes surligne la bonne ;
// - Accessibilité : le <span aria-live="polite"> n'annonce que les
//   changements de minute (propriété séparée) pour éviter le spam des
//   lecteurs d'écran.
// ===========================================================================
import { ref, computed, watch, onMounted, onBeforeUnmount } from 'vue';
import { getNextPrayer, localNowInTimezone } from '../utils/time';

const props = defineProps({
  /** Objet horaires complet renvoyé par l'API. */
  timings: { type: Object, default: null },
  /** Timezone du lieu (ex. « Europe/Paris »), renvoyée par l'API. */
  timezone: { type: String, default: null },
});

const emit = defineEmits(['next-prayer']);

/** Secondes écoulées depuis minuit dans la timezone du lieu (mise à jour 1 s). */
const nowSeconds = ref(secondsOfDayInTimezone());

let intervalId = null;

/** Heure courante du lieu, en secondes depuis minuit. */
function secondsOfDayInTimezone() {
  const now = localNowInTimezone(props.timezone);
  return now.hours * 3600 + now.minutes * 60 + now.seconds;
}

onMounted(() => {
  // Tick chaque seconde : seule la valeur nowSeconds change, les computed
  // (prochaine prière, temps restant) se recalculent automatiquement.
  intervalId = setInterval(() => {
    nowSeconds.value = secondsOfDayInTimezone();
  }, 1000);
});

onBeforeUnmount(() => {
  if (intervalId) {
    clearInterval(intervalId);
    intervalId = null;
  }
});

/** Prochaine prière à venir (ou null si toutes passées). */
const nextPrayer = computed(() => {
  // nowSeconds est lu pour créer la dépendance réactive au tick.
  void nowSeconds.value;
  return getNextPrayer(props.timings, props.timezone);
});

/** Temps restant avant la prochaine prière : { hours, minutes, seconds }. */
const remaining = computed(() => {
  const next = nextPrayer.value;
  if (!next) return null;
  const [hours, minutes] = next.time.split(':').map(Number);
  const diff = Math.max(0, hours * 3600 + minutes * 60 - nowSeconds.value);
  return {
    hours: Math.floor(diff / 3600),
    minutes: Math.floor((diff % 3600) / 60),
    seconds: diff % 60,
  };
});

// Propagation du nom de la prochaine prière au composant parent (grille).
watch(
  nextPrayer,
  (value) => {
    emit('next-prayer', value?.name ?? null);
  },
  { immediate: true }
);

/** Libellé visible complet : « Asr dans 2 h 14 min 36 s ». */
const displayText = computed(() => {
  if (!nextPrayer.value) {
    return 'Toutes les prières du jour sont passées — à demain pour Fajr, in cha Allah.';
  }
  const remainingValue = remaining.value;
  const parts = [];
  if (remainingValue.hours > 0) parts.push(`${remainingValue.hours} h`);
  if (remainingValue.minutes > 0 || remainingValue.hours > 0) {
    parts.push(`${remainingValue.minutes} min`);
  }
  parts.push(`${remainingValue.seconds} s`);
  return `Prochaine prière : ${nextPrayer.value.name} dans ${parts.join(' ')}`;
});

/** Texte annoncé aux lecteurs d'écran (niveau minute, sans les secondes). */
const ariaText = ref('');

watch(
  remaining,
  (value) => {
    if (!value) {
      ariaText.value = 'Aucune prière à venir aujourd\'hui.';
      return;
    }
    // Mise à jour de l'annonce UNIQUEMENT aux changements de minute
    // (les secondes sont trop verbeuses pour les lecteurs d'écran).
    if (value.seconds === 0 || ariaText.value === '') {
      const minutes = Math.floor((value.hours * 3600 + value.minutes * 60) / 60);
      ariaText.value = `Prochaine prière : ${nextPrayer.value.name} dans ${minutes} min`;
    }
  },
  { immediate: true }
);
</script>

<template>
  <div class="card pc-countdown-card shadow-sm">
    <div class="card-body text-center py-3">
      <!-- Texte visible : mis à jour chaque seconde -->
      <p class="mb-0 pc-countdown-text">{{ displayText }}</p>
      <!-- Annonce aux lecteurs d'écran : uniquement aux changements de minute -->
      <span class="visually-hidden" aria-live="polite">{{ ariaText }}</span>
    </div>
  </div>
</template>

<style scoped>
/* Fond vert de marque, texte blanc AA */
.pc-countdown-card {
  background-color: var(--pc-green);
  border: none;
  border-radius: 0.75rem;
}

.pc-countdown-text {
  color: #ffffff;
  font-size: 1.1rem;
  font-weight: 600;
  font-variant-numeric: tabular-nums;
}
</style>
