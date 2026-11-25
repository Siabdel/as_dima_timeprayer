<script setup>
// ===========================================================================
// RamadanCalendar : calendrier du mois sacré de Ramadan pour le lieu choisi.
// - Dates clés (1er jour, 10 dernières nuits, Nuit du Destin, Aïd) ;
// - tableau des 29/30 jours : Imsak, Fajr, lever, Dhuhr, Asr, Maghrib
//   (rupture du jeûne / iftar), Isha ; jour courant surligné.
// Données : GET /prayer-times/ramadan/ (lieu, méthode et madhhab = Réglages).
// ===========================================================================
import { ref, computed, onMounted } from 'vue';
import { usePrayerTimesStore } from '../stores/prayerTimes';
import { getRamadanCalendar } from '../api/prayerTimes';

const store = usePrayerTimesStore();
const data = ref(null);
const loading = ref(false);
const error = ref(null);
const hijriYear = ref(null); // null = Ramadan en cours / prochain (choisi par le serveur)

const coords = computed(() => {
  const l = store.location;
  return l && l.latitude != null && l.longitude != null ? l : null;
});

async function load() {
  if (!coords.value) return;
  loading.value = true;
  error.value = null;
  try {
    const params = {
      latitude: coords.value.latitude,
      longitude: coords.value.longitude,
      method: store.method,
      madhhab: store.madhhab,
    };
    if (hijriYear.value) params.hijri_year = hijriYear.value;
    const res = await getRamadanCalendar(params);
    data.value = res.data;
    hijriYear.value = res.data.hijri_year;
  } catch (e) {
    data.value = null;
    error.value =
      e?.response?.data?.error?.message ||
      'Impossible de charger le calendrier de Ramadan. Vérifiez votre connexion et réessayez.';
  } finally {
    loading.value = false;
  }
}

onMounted(() => {
  store.restorePersisted();
  load();
});

function shiftYear(delta) {
  hijriYear.value = (hijriYear.value || 1448) + delta;
  load();
}

const todayIso = (() => {
  const d = new Date();
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
})();

const fmt = (iso, opts) =>
  new Intl.DateTimeFormat('fr-FR', opts).format(new Date(`${iso}T12:00:00`));
const fmtLong = (iso) => fmt(iso, { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' });
const fmtShort = (iso) => fmt(iso, { weekday: 'short', day: 'numeric', month: 'short' });

function daysUntil(iso) {
  const diff = Math.round((new Date(`${iso}T00:00:00`) - new Date(`${todayIso}T00:00:00`)) / 86400000);
  if (diff === 0) return "Aujourd'hui";
  if (diff === 1) return 'Demain';
  return diff > 1 ? `Dans ${diff} jours` : '';
}

const todayRow = computed(() => data.value?.days.find((d) => d.date === todayIso) || null);
const nextKey = computed(() => data.value?.key_dates.find((k) => k.date >= todayIso) || null);
</script>

<template>
  <div>
    <div v-if="!coords" class="alert alert-info" role="status">
      <i class="bi bi-geo-alt me-1" aria-hidden="true"></i>
      Choisissez votre position (avec coordonnées) pour afficher les horaires de Ramadan.
      <router-link class="alert-link" :to="{ name: 'settings' }">Ouvrir les réglages</router-link>
    </div>

    <template v-else>
      <div class="card shadow-sm mb-4">
        <div class="card-body p-3 p-md-4 d-flex flex-wrap align-items-center justify-content-between gap-2">
          <div>
            <p class="text-muted small mb-0">
              <i class="bi bi-geo-alt me-1" aria-hidden="true"></i>
              {{ coords.label || `${Number(coords.latitude).toFixed(2)}, ${Number(coords.longitude).toFixed(2)}` }}
              · méthode {{ store.method }}
            </p>
            <h2 class="h5 mb-0" v-if="hijriYear">Ramadan {{ hijriYear }} AH
              <span class="arabic-text" lang="ar">رمضان</span></h2>
          </div>
          <div class="btn-group" role="group" aria-label="Changer d'année hégirienne">
            <button type="button" class="btn btn-sm btn-outline-secondary" @click="shiftYear(-1)"
                    :disabled="loading">‹ {{ (hijriYear || 0) - 1 }}</button>
            <button type="button" class="btn btn-sm btn-outline-secondary" @click="shiftYear(1)"
                    :disabled="loading">{{ (hijriYear || 0) + 1 }} ›</button>
          </div>
        </div>
      </div>

      <div v-if="error" class="alert alert-danger" role="alert">
        {{ error }}
        <button class="btn btn-outline-secondary btn-sm ms-2" type="button" @click="load">Réessayer</button>
      </div>
      <div v-if="loading" class="text-center py-5" role="status">
        <div class="spinner-border pc-spinner" aria-hidden="true"></div>
        <p class="text-muted mt-3 mb-0">Chargement du calendrier de Ramadan…</p>
      </div>

      <template v-else-if="data">
        <p class="text-muted">
          Du <strong>{{ fmtLong(data.start_date) }}</strong> au
          <strong>{{ fmtLong(data.end_date) }}</strong> ({{ data.days_count }} jours).
        </p>

        <div v-if="data.stale" class="alert alert-warning py-2" role="status">
          Données conservées : la source est momentanément indisponible.
        </div>

        <!-- Aujourd'hui -->
        <div v-if="todayRow" class="card pc-ram-today shadow-sm mb-4">
          <div class="card-body p-3 d-flex flex-wrap gap-4 align-items-center">
            <div>
              <p class="small mb-0 opacity-75">Aujourd'hui · jour {{ todayRow.hijri_day }}</p>
              <p class="h6 mb-0">{{ fmtLong(todayRow.date) }}</p>
            </div>
            <div><span class="small opacity-75">Imsak</span><br /><strong class="h5">{{ todayRow.imsak }}</strong></div>
            <div><span class="small opacity-75">Rupture du jeûne</span><br /><strong class="h5">{{ todayRow.maghrib }}</strong></div>
          </div>
        </div>

        <!-- Dates importantes -->
        <section class="mb-4" aria-labelledby="ram-key-title">
          <h3 id="ram-key-title" class="h5 mb-3">
            <i class="bi bi-stars me-1" aria-hidden="true"></i>Dates importantes
          </h3>
          <div class="row g-3">
            <div v-for="k in data.key_dates" :key="k.id" class="col-12 col-md-6">
              <div class="card h-100 shadow-sm" :class="{ 'pc-ram-highlight': k.highlight }">
                <div class="card-body p-3">
                  <div class="d-flex justify-content-between align-items-start gap-2 mb-1">
                    <span class="badge pc-ram-badge">{{ daysUntil(k.date) || fmtShort(k.date) }}</span>
                    <span v-if="k === nextKey" class="badge bg-warning text-dark">À venir</span>
                  </div>
                  <h4 class="h6 mb-0">{{ k.name }}</h4>
                  <p class="arabic-text mb-1" lang="ar">{{ k.name_ar }}</p>
                  <p class="small fw-semibold mb-1">
                    <i class="bi bi-calendar3 me-1" aria-hidden="true"></i>
                    <template v-if="k.night">Soir du {{ fmtLong(k.date) }}
                      <span class="text-muted fw-normal">(nuit du {{ k.hijri_day }} Ramadan)</span></template>
                    <template v-else>{{ fmtLong(k.date) }}</template>
                  </p>
                  <p class="text-muted small mb-0">{{ k.description }}</p>
                </div>
              </div>
            </div>
          </div>
          <p class="text-muted small mt-2 mb-0">
            Les dates dépendent de l'observation de la lune et peuvent varier d'un jour selon le pays.
            Une nuit commence au coucher du soleil.
          </p>
        </section>

        <!-- Horaires jour par jour -->
        <section aria-labelledby="ram-days-title">
          <h3 id="ram-days-title" class="h5 mb-3">
            <i class="bi bi-clock-history me-1" aria-hidden="true"></i>Horaires jour par jour
          </h3>
          <div class="card shadow-sm">
            <div class="table-responsive">
              <table class="table table-sm table-hover align-middle mb-0 pc-ram-table">
                <thead>
                  <tr>
                    <th scope="col">Jour</th><th scope="col">Date</th>
                    <th scope="col" class="text-success">Imsak</th>
                    <th scope="col">Fajr</th><th scope="col">Lever</th><th scope="col">Dhuhr</th>
                    <th scope="col">Asr</th>
                    <th scope="col" class="text-success">Rupture</th>
                    <th scope="col">Isha</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="d in data.days" :key="d.date" :class="{ 'pc-ram-row-today': d.date === todayIso }"
                      :aria-current="d.date === todayIso ? 'date' : undefined">
                    <th scope="row">{{ d.hijri_day }}</th>
                    <td class="text-nowrap text-capitalize">{{ fmtShort(d.date) }}</td>
                    <td class="fw-semibold">{{ d.imsak }}</td>
                    <td>{{ d.fajr }}</td><td>{{ d.sunrise }}</td><td>{{ d.dhuhr }}</td><td>{{ d.asr }}</td>
                    <td class="fw-semibold">{{ d.maghrib }}</td>
                    <td>{{ d.isha }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
          <p class="text-muted small mt-2 mb-0">
            Horaires calculés pour votre position avec la méthode choisie dans les réglages
            (fuseau {{ data.timezone || 'du lieu' }}).
          </p>
        </section>
      </template>
    </template>
  </div>
</template>

<style scoped>
.pc-spinner { width: 2.5rem; height: 2.5rem; color: var(--pc-green); }
.pc-ram-today { background: var(--pc-green-dark, #0d4f4b); color: #fff; }
.pc-ram-badge { background: rgba(20, 116, 111, 0.12); color: var(--pc-green-dark); font-weight: 600; }
.pc-ram-highlight { border-left: 4px solid var(--pc-gold-dark, #b8860b); }
.pc-ram-table { font-variant-numeric: tabular-nums; font-size: 0.9rem; white-space: nowrap; }
.pc-ram-row-today > * { background: rgba(184, 134, 11, 0.18) !important; font-weight: 700; }
</style>
