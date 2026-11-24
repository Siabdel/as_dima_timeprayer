<script setup>
// ===========================================================================
// PrayerTimesCard : grille des 6 cartes d'horaires (Fajr → Isha).
// ---------------------------------------------------------------------------
// - Nom français + nom arabe (police Amiri, RTL) ;
// - La carte de la prochaine prière est mise en évidence (bordure dorée
//   --pc-gold + badge « Prochaine ») ;
// - Accessibilité : aria-label sur chaque carte (« Fajr à 05:23 »).
// ===========================================================================
const props = defineProps({
  /** Objet horaires renvoyé par l'API : { fajr, sunrise, dhuhr, asr, maghrib, isha }. */
  timings: { type: Object, default: null },
  /** Clé de la prochaine prière ('fajr', 'sunrise', ...) ou null. */
  nextPrayer: { type: String, default: null },
});

// Définition statique des 6 prières : libellé français, nom arabe, pictogramme.
const cards = [
  { key: 'fajr', label: 'Fajr', arabic: 'الفجر', emoji: '🌅' },
  { key: 'sunrise', label: 'Lever du soleil', arabic: 'الشروق', emoji: '☀️' },
  { key: 'dhuhr', label: 'Dhuhr', arabic: 'الظهر', emoji: '☀️' },
  { key: 'asr', label: 'Asr', arabic: 'العصر', emoji: '🌤️' },
  { key: 'maghrib', label: 'Maghrib', arabic: 'المغرب', emoji: '🌇' },
  { key: 'isha', label: 'Isha', arabic: 'العشاء', emoji: '🌙' },
];

/** Heure affichée pour une prière (ou un tiret si absente). */
function timeOf(card) {
  return props.timings?.[card.key] ?? '—';
}

/** aria-label de la carte, ex. « Fajr à 05:23 ». */
function ariaLabel(card) {
  return `${card.label} à ${timeOf(card)}`;
}
</script>

<template>
  <div class="row g-3 row-cols-2 row-cols-md-3 row-cols-lg-6">
    <div v-for="card in cards" :key="card.key" class="col">
      <div
        class="card h-100 pc-prayer-card"
        :class="{ 'pc-next-prayer': nextPrayer === card.key }"
        :aria-label="ariaLabel(card)"
      >
        <div class="card-body text-center py-3">
          <span v-if="nextPrayer === card.key" class="badge pc-badge-next mb-1">
            Prochaine
          </span>
          <div class="pc-prayer-emoji" aria-hidden="true">{{ card.emoji }}</div>
          <div class="fw-semibold">{{ card.label }}</div>
          <div class="arabic-text pc-arabic-small" lang="ar">{{ card.arabic }}</div>
          <div class="pc-prayer-time">{{ timeOf(card) }}</div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* Carte prière : fond blanc, coin arrondi discret */
.pc-prayer-card {
  border-radius: 0.75rem;
}

/* Carte de la prochaine prière : bordure dorée (accent visuel) */
.pc-next-prayer {
  border: 2px solid var(--pc-gold);
  background-color: rgba(233, 196, 106, 0.12);
}

/* Badge « Prochaine » : or sur fond vert (contraste AA vérifié) */
.pc-badge-next {
  background-color: var(--pc-green);
  color: var(--pc-gold);
  font-weight: 600;
}

.pc-prayer-emoji {
  font-size: 1.75rem;
  line-height: 1.2;
}

/* Nom arabe : version compacte de la classe .arabic-text (Amiri, RTL) */
.pc-arabic-small {
  font-size: 1.15rem;
  line-height: 1.7;
  margin-top: 0.15rem;
}

/* Heure en gros, vert de marque (AA sur blanc) */
.pc-prayer-time {
  font-size: 1.5rem;
  font-weight: 600;
  color: var(--pc-green);
  font-variant-numeric: tabular-nums;
  margin-top: 0.25rem;
}
</style>
