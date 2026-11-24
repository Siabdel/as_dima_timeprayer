<script setup>
// ===========================================================================
// FranceCalendar : calendrier grégorien avec les jours fériés en France.
// - Sélecteur d'année ; liste des jours fériés (jour de la semaine, « dans X
//   jours ») ; 12 mois en grille (lundi en premier), fériés surlignés, jour
//   courant cerclé. Données : GET /events/france/.
// ===========================================================================
import { ref, computed, watch } from 'vue';
import { getFranceHolidays } from '../api/events';

const props = defineProps({ initialYear: { type: Number, default: new Date().getFullYear() } });

const YEARS = Array.from({ length: 9 }, (_, i) => 2024 + i);
const year = ref(YEARS.includes(props.initialYear) ? props.initialYear : new Date().getFullYear());
const holidays = ref([]);
const loading = ref(true);
const error = ref(null);

async function load() {
  loading.value = true;
  error.value = null;
  try {
    const { data } = await getFranceHolidays(year.value);
    holidays.value = Array.isArray(data?.holidays) ? data.holidays : [];
  } catch {
    error.value = 'Impossible de charger les jours fériés. Vérifiez votre connexion et réessayez.';
    holidays.value = [];
  } finally {
    loading.value = false;
  }
}
watch(year, load, { immediate: true });

const todayIso = (() => {
  const d = new Date();
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
})();

const byDate = computed(() => new Map(holidays.value.map((h) => [h.date, h])));

const fmtLong = (iso) =>
  new Intl.DateTimeFormat('fr-FR', { weekday: 'long', day: 'numeric', month: 'long' }).format(
    new Date(`${iso}T12:00:00`)
  );

function daysUntil(iso) {
  const diff = Math.round((new Date(`${iso}T00:00:00`) - new Date(`${todayIso}T00:00:00`)) / 86400000);
  if (diff === 0) return "Aujourd'hui";
  if (diff === 1) return 'Demain';
  return diff > 1 ? `Dans ${diff} jours` : '';
}

/** 12 mois : { label, cells: [{ day, iso } | null] } (semaine du lundi). */
const months = computed(() =>
  Array.from({ length: 12 }, (_, m) => {
    const first = new Date(year.value, m, 1);
    const offset = (first.getDay() + 6) % 7; // lundi = 0
    const count = new Date(year.value, m + 1, 0).getDate();
    const cells = Array(offset).fill(null);
    for (let day = 1; day <= count; day += 1) {
      const iso = `${year.value}-${String(m + 1).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
      cells.push({ day, iso });
    }
    return {
      label: new Intl.DateTimeFormat('fr-FR', { month: 'long' }).format(first),
      cells,
    };
  })
);
const WEEKDAYS = ['L', 'M', 'M', 'J', 'V', 'S', 'D'];
</script>

<template>
  <div>
    <div class="card shadow-sm mb-4">
      <div class="card-body p-3 p-md-4">
        <label for="pc-france-year" class="form-label">
          <i class="bi bi-calendar3 me-1" aria-hidden="true"></i>Année grégorienne
        </label>
        <select id="pc-france-year" v-model.number="year" class="form-select w-auto">
          <option v-for="y in YEARS" :key="y" :value="y">{{ y }}</option>
        </select>
      </div>
    </div>

    <div v-if="error" class="alert alert-danger" role="alert">
      {{ error }}
      <button class="btn btn-outline-secondary btn-sm ms-2" type="button" @click="load">Réessayer</button>
    </div>
    <div v-if="loading" class="text-center py-5" role="status">
      <div class="spinner-border pc-spinner" aria-hidden="true"></div>
    </div>

    <template v-else-if="!error">
      <!-- Liste des jours fériés -->
      <section class="mb-4" aria-labelledby="fr-holidays-title">
        <h2 id="fr-holidays-title" class="h5 mb-3">
          <i class="bi bi-flag me-1" aria-hidden="true"></i>Jours fériés {{ year }} — France
        </h2>
        <div class="card shadow-sm">
          <ul class="list-group list-group-flush">
            <li v-for="h in holidays" :key="h.id" class="list-group-item d-flex flex-wrap gap-2 align-items-start">
              <div class="pc-fr-date flex-shrink-0 text-capitalize">{{ fmtLong(h.date) }}</div>
              <div class="flex-grow-1">
                <span class="fw-semibold">{{ h.name }}</span>
                <span v-if="h.regional" class="badge bg-secondary ms-2">Alsace-Moselle</span>
                <span v-if="daysUntil(h.date)" class="badge pc-fr-days ms-2">{{ daysUntil(h.date) }}</span>
                <p class="text-muted small mb-0">{{ h.description }}</p>
              </div>
            </li>
          </ul>
        </div>
      </section>

      <!-- Calendrier de l'année -->
      <section aria-labelledby="fr-grid-title">
        <h2 id="fr-grid-title" class="h5 mb-3">
          <i class="bi bi-calendar-week me-1" aria-hidden="true"></i>Calendrier {{ year }}
        </h2>
        <div class="row g-3">
          <div v-for="m in months" :key="m.label" class="col-12 col-sm-6 col-lg-4">
            <div class="card shadow-sm h-100">
              <div class="card-body p-3">
                <h3 class="h6 text-capitalize pc-fr-month mb-2">{{ m.label }}</h3>
                <div class="pc-fr-grid" role="grid" :aria-label="`${m.label} ${year}`">
                  <span v-for="(d, i) in WEEKDAYS" :key="`h${i}`" class="pc-fr-wd">{{ d }}</span>
                  <template v-for="(c, i) in m.cells" :key="i">
                    <span v-if="!c" class="pc-fr-cell"></span>
                    <span v-else class="pc-fr-cell"
                          :class="{ holiday: byDate.has(c.iso) && !byDate.get(c.iso).regional,
                                    regional: byDate.has(c.iso) && byDate.get(c.iso).regional,
                                    today: c.iso === todayIso }"
                          :title="byDate.get(c.iso)?.name"
                          :aria-label="byDate.get(c.iso) ? `${c.day} : ${byDate.get(c.iso).name}` : undefined">
                      {{ c.day }}
                    </span>
                  </template>
                </div>
              </div>
            </div>
          </div>
        </div>
        <p class="text-muted small mt-2 mb-0">
          <span class="pc-fr-legend holiday"></span> Jour férié ·
          <span class="pc-fr-legend regional"></span> Alsace-Moselle uniquement ·
          <span class="pc-fr-legend today"></span> Aujourd'hui
        </p>
      </section>
    </template>
  </div>
</template>

<style scoped>
.pc-spinner { width: 2.5rem; height: 2.5rem; color: var(--pc-green); }
.pc-fr-date { min-width: 11rem; color: #0b3d91; font-weight: 600; }
.pc-fr-days { background: rgba(11, 61, 145, 0.1); color: #0b3d91; font-weight: 600; }
.pc-fr-month { color: var(--pc-green); }
.pc-fr-grid { display: grid; grid-template-columns: repeat(7, 1fr); gap: 2px; text-align: center; font-size: 0.85rem; }
.pc-fr-wd { color: #6c757d; font-size: 0.75rem; }
.pc-fr-cell { padding: 0.2rem 0; border-radius: 50%; min-height: 1.8rem; line-height: 1.4rem; font-variant-numeric: tabular-nums; }
.pc-fr-cell.holiday { background: #0b3d91; color: #fff; font-weight: 600; }
.pc-fr-cell.regional { background: #dbe4f5; color: #0b3d91; }
.pc-fr-cell.today { outline: 2px solid var(--pc-gold-dark, #b8860b); outline-offset: -2px; font-weight: 700; }
.pc-fr-legend { display: inline-block; width: 0.8rem; height: 0.8rem; border-radius: 50%; vertical-align: middle; }
.pc-fr-legend.holiday { background: #0b3d91; }
.pc-fr-legend.regional { background: #dbe4f5; border: 1px solid #0b3d91; }
.pc-fr-legend.today { outline: 2px solid var(--pc-gold-dark, #b8860b); outline-offset: -2px; }
</style>
