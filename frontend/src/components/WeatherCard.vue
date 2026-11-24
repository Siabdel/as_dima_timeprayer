<script setup>
// ===========================================================================
// WeatherCard : météo du lieu courant, sous « Horaires du jour ».
// - Résumé : icône, température (°C | °F), précipitations / humidité / vent ;
// - Onglets Température / Précipitations / Vent : courbe sur 24 h (SVG) ;
// - Prévisions sur 8 jours (clic = détail du jour dans l'en-tête).
// Données : GET /weather/ (Open-Meteo via le backend). Échec = carte masquée.
// ===========================================================================
import { ref, computed, watch } from 'vue';
import { getWeather } from '../api/weather';

const props = defineProps({
  /** Lieu courant du store : { latitude, longitude } ou { city, country }. */
  location: { type: Object, default: null },
});

const data = ref(null);
const loading = ref(false);
const failed = ref(false);
const unit = ref('C'); // 'C' | 'F'
const tab = ref('temp'); // 'temp' | 'precip' | 'wind'
const selectedDay = ref(0);
let requestId = 0;

const TABS = [
  { key: 'temp', label: 'Température' },
  { key: 'precip', label: 'Précipitations' },
  { key: 'wind', label: 'Vent' },
];

async function load() {
  const loc = props.location;
  if (!loc) {
    data.value = null;
    return;
  }
  const params =
    loc.latitude != null && loc.longitude != null
      ? { latitude: loc.latitude, longitude: loc.longitude, ...(loc.city ? { city: loc.city } : {}) }
      : { city: loc.city, country: loc.country ?? '' };
  const id = ++requestId;
  loading.value = true;
  failed.value = false;
  try {
    const response = await getWeather(params);
    if (id !== requestId) return;
    data.value = response.data;
    selectedDay.value = 0;
  } catch {
    if (id === requestId) {
      data.value = null;
      failed.value = true;
    }
  } finally {
    if (id === requestId) loading.value = false;
  }
}
watch(() => props.location, load, { immediate: true, deep: true });

// --- Conversions / libellés ------------------------------------------------------
const toUnit = (c) => (c == null ? null : Math.round(unit.value === 'F' ? c * 9 / 5 + 32 : c));
const both = (c) => (c == null ? '—' : `${Math.round(c)}° ${Math.round(c * 9 / 5 + 32)}°`);

const ICONS = [
  [[0], 'bi-sun'],
  [[1, 2], 'bi-cloud-sun'],
  [[3], 'bi-cloud'],
  [[45, 48], 'bi-cloud-fog2'],
  [[51, 53, 55, 56, 57], 'bi-cloud-drizzle'],
  [[61, 63, 65, 66, 67], 'bi-cloud-rain'],
  [[80, 81, 82], 'bi-cloud-rain-heavy'],
  [[71, 73, 75, 77, 85, 86], 'bi-cloud-snow'],
  [[95, 96, 99], 'bi-cloud-lightning-rain'],
];
const iconFor = (code) => ICONS.find(([codes]) => codes.includes(code))?.[1] ?? 'bi-cloud';

const place = computed(() => data.value?.location?.name || props.location?.city || 'Ma position');
const current = computed(() => data.value?.current ?? null);

const weekday = (iso, long = false) =>
  new Intl.DateTimeFormat('fr-FR', { weekday: long ? 'long' : 'short', timeZone: 'UTC' })
    .format(new Date(`${iso}T12:00:00Z`))
    .replace('.', '');

const headerLine = computed(() => {
  if (!current.value) return '';
  const day = data.value.daily[selectedDay.value];
  if (selectedDay.value === 0 || !day) {
    const t = String(current.value.time ?? '');
    const iso = t.slice(0, 10);
    return `${iso ? weekday(iso, true) : ''} ${t.slice(11, 16).replace(':00', ':00')}`.trim();
  }
  return weekday(day.date, true);
});
const headerLabel = computed(() => {
  if (selectedDay.value === 0) return current.value?.label ?? '';
  return ''; // libellé du jour non fourni par l'API pour les jours suivants
});

// --- Graphique (SVG, 9 points sur 24 h) --------------------------------------------
const W = 600;
const H = 110;
const PAD_TOP = 22;
const series = computed(() => {
  const points = data.value?.hourly ?? [];
  return points.map((p) => {
    const raw =
      tab.value === 'temp' ? toUnit(p.temp_c) : tab.value === 'precip' ? p.precip_prob : p.wind_kmh;
    return { raw: raw ?? 0, time: p.time };
  });
});
const chart = computed(() => {
  const s = series.value;
  if (s.length < 2) return null;
  const min = Math.min(...s.map((p) => p.raw));
  const max = Math.max(...s.map((p) => p.raw));
  const span = max - min || 1;
  const xs = (i) => (i / (s.length - 1)) * W;
  const ys = (v) => PAD_TOP + (1 - (v - min) / span) * (H - PAD_TOP - 8);
  const pts = s.map((p, i) => ({ x: xs(i), y: ys(p.raw), v: p.raw, t: p.time }));
  const line = pts.map((p, i) => `${i ? 'L' : 'M'}${p.x.toFixed(1)},${p.y.toFixed(1)}`).join(' ');
  return { pts, line, area: `${line} L${W},${H} L0,${H} Z` };
});
const hourLabel = (iso) => `${String(iso).slice(11, 13)}:00`;
const chartUnit = computed(() => (tab.value === 'precip' ? '%' : tab.value === 'wind' ? '' : '°'));
</script>

<template>
  <section v-if="current" class="pc-weather" aria-label="Météo">
    <!-- Résumé -->
    <div class="d-flex flex-wrap justify-content-between gap-3">
      <div class="d-flex align-items-center gap-3">
        <i class="bi pc-weather-icon" :class="iconFor(current.code)" aria-hidden="true"></i>
        <div class="d-flex align-items-start">
          <span class="pc-weather-temp">{{ toUnit(current.temp_c) }}</span>
          <span class="pc-weather-units" role="group" aria-label="Unité de température">
            <button type="button" :class="{ on: unit === 'C' }" :aria-pressed="unit === 'C'" @click="unit = 'C'">°C</button>
            <span aria-hidden="true">|</span>
            <button type="button" :class="{ on: unit === 'F' }" :aria-pressed="unit === 'F'" @click="unit = 'F'">°F</button>
          </span>
        </div>
        <ul class="list-unstyled small mb-0 pc-weather-details">
          <li v-if="current.precip_prob != null">Précipitations : {{ current.precip_prob }}%</li>
          <li v-if="current.humidity != null">Humidité : {{ current.humidity }}%</li>
          <li v-if="current.wind_kmh != null">Vent : {{ current.wind_kmh }} km/h</li>
        </ul>
      </div>
      <div class="text-end">
        <div class="h5 mb-0">Météo</div>
        <div class="pc-weather-muted">{{ place }}</div>
        <div class="pc-weather-muted text-capitalize">{{ headerLine }}</div>
        <div class="pc-weather-muted">{{ headerLabel }}</div>
      </div>
    </div>

    <!-- Onglets -->
    <div class="pc-weather-tabs" role="tablist">
      <button v-for="t in TABS" :id="`wtab-${t.key}`" :key="t.key" type="button" role="tab"
              :aria-selected="tab === t.key" :class="{ on: tab === t.key }" @click="tab = t.key">
        {{ t.label }}
      </button>
    </div>

    <!-- Courbe -->
    <div v-if="chart" class="pc-weather-chart" role="img"
         :aria-label="`Courbe ${TABS.find((t) => t.key === tab).label} sur 24 heures`">
      <svg :viewBox="`0 0 ${W} ${H}`" preserveAspectRatio="none">
        <path :d="chart.area" class="area" />
        <path :d="chart.line" class="line" fill="none" />
      </svg>
      <div class="pc-weather-points">
        <span v-for="(p, i) in chart.pts" :key="p.t" class="pt"
              :style="{ left: `${(p.x / W) * 100}%`, top: `${(p.y / H) * 100}%` }"
              :class="{ first: i === 0, last: i === chart.pts.length - 1 }">
          {{ p.v }}{{ chartUnit }}
        </span>
      </div>
      <div class="pc-weather-hours">
        <span v-for="p in chart.pts" :key="p.t">{{ hourLabel(p.t) }}</span>
      </div>
    </div>

    <!-- Prévisions sur 8 jours -->
    <ul class="pc-weather-days list-unstyled mb-0">
      <li v-for="(d, i) in data.daily" :key="d.date">
        <button type="button" :class="{ on: selectedDay === i }" :aria-pressed="selectedDay === i"
                @click="selectedDay = i">
          <span class="d-block">{{ i === 0 ? weekday(d.date) : weekday(d.date) }}</span>
          <i class="bi d-block my-1" :class="iconFor(d.code)" aria-hidden="true"></i>
          <span class="d-block small">
            {{ unit === 'C' ? Math.round(d.temp_max_c) : toUnit(d.temp_max_c) }}°
            <span class="pc-weather-muted">{{ unit === 'C' ? Math.round(d.temp_min_c) : toUnit(d.temp_min_c) }}°</span>
          </span>
        </button>
      </li>
    </ul>
  </section>

  <div v-else-if="loading" class="pc-weather pc-weather-muted text-center" role="status">
    Chargement de la météo…
  </div>
</template>

<style scoped>
.pc-weather {
  --w-bg: #202124;
  --w-fg: #e8eaed;
  --w-muted: #9aa0a6;
  --w-accent: #fdd663;
  background: var(--w-bg);
  color: var(--w-fg);
  border-radius: 1rem;
  padding: 1.25rem;
  margin-top: 1.5rem;
}
.pc-weather-muted { color: var(--w-muted); }
.pc-weather-icon { font-size: 3.5rem; color: var(--w-accent); line-height: 1; }
.pc-weather-temp { font-size: 3rem; line-height: 1; }
.pc-weather-units { font-size: 0.9rem; color: var(--w-muted); margin-top: 0.2rem; margin-left: 0.2rem; }
.pc-weather-units button {
  background: none; border: 0; padding: 0 0.15rem; color: var(--w-muted); cursor: pointer;
}
.pc-weather-units button.on { color: var(--w-fg); font-weight: 600; }
.pc-weather-details { color: var(--w-muted); font-size: 0.8rem; }

.pc-weather-tabs { display: flex; gap: 1rem; margin: 1rem 0 0.5rem; border-bottom: 1px solid #3c4043; }
.pc-weather-tabs button {
  background: none; border: 0; border-bottom: 2px solid transparent; color: var(--w-muted);
  padding: 0.35rem 0; cursor: pointer;
}
.pc-weather-tabs button.on { color: var(--w-fg); border-bottom-color: var(--w-accent); }

.pc-weather-chart { position: relative; padding: 0 1.25rem; margin-top: 0.5rem; }
.pc-weather-chart svg { display: block; width: 100%; height: 110px; }
.pc-weather-chart .area { fill: rgba(253, 214, 99, 0.18); }
.pc-weather-chart .line { stroke: var(--w-accent); stroke-width: 2; vector-effect: non-scaling-stroke; }
.pc-weather-points { position: absolute; inset: 0 1.25rem auto 1.25rem; height: 110px; pointer-events: none; }
.pc-weather-points .pt {
  position: absolute; transform: translate(-50%, -140%); font-size: 0.7rem; color: var(--w-muted);
}
.pc-weather-points .pt.first { transform: translate(0, -140%); }
.pc-weather-points .pt.last { transform: translate(-100%, -140%); }
.pc-weather-hours { display: flex; justify-content: space-between; font-size: 0.7rem; color: var(--w-muted); margin-top: 0.25rem; }

.pc-weather-days { display: flex; gap: 0.25rem; margin-top: 1rem; overflow-x: auto; }
.pc-weather-days li { flex: 1 0 3.6rem; }
.pc-weather-days button {
  width: 100%; background: none; border: 0; border-radius: 0.6rem; color: var(--w-fg);
  padding: 0.5rem 0.25rem; text-align: center; cursor: pointer; text-transform: capitalize;
}
.pc-weather-days button.on { background: #35363a; }
.pc-weather-days .bi { font-size: 1.5rem; color: var(--w-accent); }

@media (max-width: 575.98px) {
  .pc-weather-temp { font-size: 2.4rem; }
  .pc-weather-icon { font-size: 2.6rem; }
}
</style>
