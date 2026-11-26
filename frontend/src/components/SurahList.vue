<script setup>
// ===========================================================================
// SurahList : liste des 114 sourates (list-group Bootstrap).
// ---------------------------------------------------------------------------
// - Numéro dans un badge rond, nom translittéré en gras, nom arabe en
//   .arabic-text (Amiri, RTL) aligné à droite ;
// - « 7 versets · La Mecque / Médine » en sous-titre ;
// - Clic OU clavier (Entrée / Espace) → navigation vers /quran/:number ;
// - La sourate en cours de lecture est mise en évidence (bordure dorée).
// ===========================================================================
import { useRouter } from 'vue-router';
import { SURAH_STATUSES, useReadingStatusStore } from '../stores/readingStatus';

const props = defineProps({
  /** Liste des sourates (réponse de GET /quran/surahs/). */
  surahs: { type: Array, default: () => [] },
  /** Numéro de la sourate en cours de lecture (surlignage), ou null. */
  playingSurah: { type: Number, default: null },
});

const router = useRouter();
const readingStatus = useReadingStatusStore();
const statusGroups = [...new Set(SURAH_STATUSES.map((s) => s.group))];

function statusTone(surah) {
  return SURAH_STATUSES.find((s) => s.value === readingStatus.statusOf(surah.number))?.tone ?? 'none';
}

/** Libellé français du lieu de révélation. */
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

/** Sous-titre « 7 versets · La Mecque ». */
function subtitle(surah) {
  const parts = [`${surah.verses_count} verset${surah.verses_count > 1 ? 's' : ''}`];
  const place = revelationLabel(surah.revelation_place);
  if (place) parts.push(place);
  return parts.join(' · ');
}

/** aria-label explicite pour la navigation au lecteur d'écran. */
function ariaLabel(surah) {
  const place = revelationLabel(surah.revelation_place);
  return [
    `Sourate ${surah.number} : ${surah.name_transliterated}`,
    `${surah.verses_count} versets`,
    place ? `révélée à ${place}` : '',
    surah.number === props.playingSurah ? 'en cours de lecture' : '',
  ]
    .filter(Boolean)
    .join(', ');
}

/** Navigation vers la page de lecture de la sourate. */
function open(surah) {
  router.push({ name: 'surah', params: { number: surah.number } });
}
</script>

<template>
  <ol class="list-group list-group-flush pc-surah-list">
    <li
      v-for="surah in surahs"
      :key="surah.number"
      class="list-group-item pc-surah-item"
      :class="{ 'pc-surah-playing': surah.number === playingSurah }"
      role="button"
      tabindex="0"
      :aria-label="ariaLabel(surah)"
      @click="open(surah)"
      @keydown.enter.prevent="open(surah)"
      @keydown.space.prevent="open(surah)"
    >
      <div class="d-flex align-items-center gap-3">
        <!-- Numéro de la sourate : badge rond vert -->
        <span class="pc-surah-badge" aria-hidden="true">{{ surah.number }}</span>

        <div class="flex-grow-1 min-w-0">
          <div class="fw-semibold pc-surah-name">
            {{ surah.number }}. {{ surah.name_transliterated }}
          </div>
          <small class="text-muted">{{ subtitle(surah) }}</small>
        </div>

        <!-- Indicateur « en lecture » -->
        <i
          v-if="surah.number === playingSurah"
          class="bi bi-volume-up-fill pc-surah-playing-icon"
          title="Sourate en cours de lecture"
        ></i>

        <!-- Tag de statut (lecture / mémorisation), sans déclencher la navigation -->
        <select
          class="form-select form-select-sm pc-status-tag"
          :class="`pc-status-${statusTone(surah)}`"
          :value="readingStatus.statusOf(surah.number)"
          :aria-label="`Statut de la sourate ${surah.name_transliterated}`"
          @click.stop
          @keydown.stop
          @change="readingStatus.setStatus(surah.number, $event.target.value)"
        >
          <option value="">Statut…</option>
          <optgroup v-for="g in statusGroups" :key="g" :label="g">
            <option
              v-for="s in SURAH_STATUSES.filter((x) => x.group === g)"
              :key="s.value"
              :value="s.value"
            >
              {{ s.label }}
            </option>
          </optgroup>
        </select>

        <!-- Nom arabe : Amiri, RTL, aligné à droite -->
        <span class="arabic-text pc-surah-arabic" lang="ar" dir="rtl">
          {{ surah.name_arabic }}
        </span>
      </div>
    </li>
  </ol>
</template>

<style scoped>
/* Item cliquable : curseur + survol discret de marque */
.pc-surah-item {
  cursor: pointer;
  border-radius: 0.5rem;
  transition: background-color 0.15s ease;
}

.pc-surah-item:hover {
  background-color: rgba(20, 116, 111, 0.06);
}

/* Badge rond du numéro (vert de marque, texte blanc AA) */
.pc-surah-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 2.4rem;
  height: 2.4rem;
  flex: 0 0 auto;
  border-radius: 50%;
  background-color: var(--pc-green);
  color: #ffffff;
  font-weight: 600;
  font-size: 0.9rem;
}

/* Nom arabe : version compacte de .arabic-text */
.pc-surah-arabic {
  font-size: 1.3rem;
  line-height: 1.8;
  flex: 0 0 auto;
}

/* Sourate en cours de lecture : fond or pâle + bordure dorée */
.pc-surah-playing {
  background-color: rgba(233, 196, 106, 0.12);
  border: 1px solid var(--pc-gold);
}

.pc-surah-playing-icon {
  color: var(--pc-green);
  flex: 0 0 auto;
}

/* Empêche les débordements du nom sur petits écrans */
.min-w-0 {
  min-width: 0;
}

.pc-surah-name {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* Tag de statut : select compact coloré */
.pc-status-tag {
  width: auto;
  max-width: 9.5rem;
  flex: 0 0 auto;
  border-radius: 999px;
  font-size: 0.78rem;
  font-weight: 600;
}
.pc-status-none { color: #5b6665; }
.pc-status-secondary { background-color: #e9ecef; color: #343a40; }
.pc-status-warning { background-color: #fff3cd; color: #664d03; }
.pc-status-success { background-color: #d1e7dd; color: #0a3622; }
.pc-status-info { background-color: #cff4fc; color: #055160; }
.pc-status-primary { background-color: #cfe2ff; color: #052c65; }
.pc-status-danger { background-color: #f8d7da; color: #58151c; }
</style>
