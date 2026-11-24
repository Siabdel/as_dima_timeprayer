<script setup>
// ===========================================================================
// CalendarView — page « Calendrier des fêtes » (route /calendar).
// ---------------------------------------------------------------------------
// - Sélecteur d'année grégorienne (2024-2030, défaut année courante) + badge
//   de l'année hégirienne correspondante (renvoyée par le backend) ;
// - Section « Prochaines fêtes » : 6 cartes (GET /events/upcoming/?limit=6)
//   avec « dans X jours » / « aujourd'hui » et badge type (islamique = vert
//   de marque, national = rouge Maroc) ;
// - Section « Calendrier de l'année » : liste complète groupée par mois
//   (GET /events/?year=YYYY), fêtes islamiques avec leur date hégirienne ;
// - Toggle « Fêtes islamiques / Fêtes nationales / Toutes ».
// ===========================================================================
import { ref, computed, onMounted, watch } from 'vue';
import { getYearEvents, getUpcomingEvents } from '../api/events';

// ---------------------------------------------------------------------------
// État local de la vue
// ---------------------------------------------------------------------------
const YEARS = [2024, 2025, 2026, 2027, 2028, 2029, 2030];
const currentYear = new Date().getFullYear();
const selectedYear = ref(YEARS.includes(currentYear) ? currentYear : 2026);

const upcoming = ref([]); // 6 prochains événements (avec days_until)
const upcomingToday = ref(null); // « today » renvoyé par le backend
const events = ref([]); // liste complète de l'année sélectionnée
const hijriYears = ref([]); // années hégiriennes couvertes (du backend)
const loading = ref(true);
const upcomingLoading = ref(true);
const error = ref(null);

// Filtre par type : « all » | « islamic » | « national »
const filter = ref('all');

const FILTERS = [
  { value: 'all', label: 'Toutes' },
  { value: 'islamic', label: 'Fêtes islamiques' },
  { value: 'national', label: 'Fêtes nationales' },
];

// ---------------------------------------------------------------------------
// Chargement
// ---------------------------------------------------------------------------
/** Liste complète de l'année sélectionnée. */
async function loadYear() {
  loading.value = true;
  error.value = null;
  try {
    const { data } = await getYearEvents(selectedYear.value);
    events.value = Array.isArray(data?.events) ? data.events : [];
    hijriYears.value = Array.isArray(data?.hijri_years) ? data.hijri_years : [];
  } catch {
    error.value =
      'Impossible de charger le calendrier des fêtes. Vérifiez votre connexion et réessayez.';
    events.value = [];
    hijriYears.value = [];
  } finally {
    loading.value = false;
  }
}

/** 6 prochains événements (indépendant de l'année sélectionnée). */
async function loadUpcoming() {
  upcomingLoading.value = true;
  try {
    const { data } = await getUpcomingEvents(6);
    upcoming.value = Array.isArray(data?.events) ? data.events : [];
    upcomingToday.value = data?.today ?? null;
  } catch {
    // La section « Prochaines fêtes » reste vide en cas d'échec : l'alerte
    // d'erreur globale (loadYear) couvre le problème de connexion.
    upcoming.value = [];
    upcomingToday.value = null;
  } finally {
    upcomingLoading.value = false;
  }
}

onMounted(() => {
  loadYear();
  loadUpcoming();
});

watch(selectedYear, () => {
  loadYear();
});

// ---------------------------------------------------------------------------
// Helpers d'affichage
// ---------------------------------------------------------------------------
/** Badge coloré selon le type : vert de marque (islamique) / rouge Maroc. */
function typeBadgeClass(type) {
  return type === 'islamic' ? 'pc-badge-islamic' : 'pc-badge-national';
}

function typeLabel(type) {
  return type === 'islamic' ? 'Islamique' : 'Férié national';
}

/** Icône Bootstrap adaptée au type d'événement. */
function typeIcon(type) {
  return type === 'islamic' ? 'bi-moon-stars' : 'bi-flag';
}

/** « 30 juillet 2026 » en français. */
function formatDate(isoDate) {
  if (!isoDate) return '';
  try {
    return new Intl.DateTimeFormat('fr-FR', { dateStyle: 'long' }).format(
      new Date(`${isoDate}T00:00:00`)
    );
  } catch {
    return isoDate;
  }
}

/** « 1 Shawwal 1447 » (date hégirienne d'une fête islamique). */
function formatHijri(hijri) {
  if (!hijri?.month_name) return '';
  return `${hijri.day ?? ''} ${hijri.month_name} ${hijri.year ?? ''}`.trim();
}

/** « dans X jours » ou « aujourd'hui » (champ days_until du backend). */
function daysUntilLabel(days) {
  if (days === 0) return "Aujourd'hui";
  if (days === 1) return 'Demain';
  return `Dans ${days} jours`;
}

// ---------------------------------------------------------------------------
// Liste filtrée + groupée par mois
// ---------------------------------------------------------------------------
const filteredEvents = computed(() => {
  if (filter.value === 'all') return events.value;
  return events.value.filter((e) => e.type === filter.value);
});

/**
 * Liste groupée par mois : [{ month: 'janvier', label: 'janvier 2026',
 * events: [...] }]. L'API est triée par date croissante, donc l'ordre des
 * mois suit naturellement.
 */
const groupedByMonth = computed(() => {
  const groups = [];
  const byMonth = new Map();
  for (const event of filteredEvents.value) {
    const iso = event.date || '';
    const key = iso.slice(0, 7); // « YYYY-MM »
    let group = byMonth.get(key);
    if (!group) {
      // Étiquette lisible : « mars 2026 » (mois déduit de la date, ou l'année
      // sélectionnée si la date n'a pas de mois exploitable).
      let label = `${selectedYear.value}`;
      try {
        const d = new Date(`${iso}T00:00:00`);
        if (!Number.isNaN(d.getTime())) {
          label = new Intl.DateTimeFormat('fr-FR', {
            month: 'long',
            year: 'numeric',
          }).format(d);
        }
      } catch {
        // Étiquette par défaut conservée.
      }
      group = { key, label, events: [] };
      byMonth.set(key, group);
      groups.push(group);
    }
    group.events.push(event);
  }
  return groups;
});
</script>

<template>
  <div class="row justify-content-center">
    <div class="col-12 col-lg-10 col-xl-9">
      <h1 class="h4 mb-1">Calendrier des fêtes</h1>
      <p class="text-muted mb-4">
        Fêtes islamiques et jours fériés nationaux (Maroc), par année.
      </p>

      <!-- ===================== En-tête : année + badge hégirien ===================== -->
      <div class="card shadow-sm mb-4">
        <div class="card-body p-3 p-md-4">
          <div class="row g-3 align-items-center">
            <div class="col-12 col-md-6">
              <label for="pc-calendar-year" class="form-label">
                <i class="bi bi-calendar3 me-1" aria-hidden="true"></i>
                Année grégorienne
              </label>
              <select
                id="pc-calendar-year"
                v-model.number="selectedYear"
                class="form-select"
                aria-label="Sélectionner l'année grégorienne"
              >
                <option v-for="y in YEARS" :key="y" :value="y">{{ y }}</option>
              </select>
            </div>
            <div class="col-12 col-md-6">
              <p class="form-label mb-1 text-muted">
                <i class="bi bi-moon-stars me-1" aria-hidden="true"></i>
                Année(s) hégirienne(s) couverte(s)
              </p>
              <div>
                <span
                  v-for="hy in hijriYears"
                  :key="hy"
                  class="badge pc-badge-hijri me-1"
                >
                  {{ hy }} AH
                </span>
                <span v-if="!hijriYears.length" class="text-muted small">
                  —
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Erreur de chargement -->
      <div v-if="error" class="alert alert-danger" aria-live="polite" role="alert">
        <i class="bi bi-x-octagon me-1" aria-hidden="true"></i>
        {{ error }}
        <button class="btn btn-outline-secondary btn-sm ms-2" type="button" @click="loadYear">
          Réessayer
        </button>
      </div>

      <!-- Chargement -->
      <div v-if="loading" class="text-center py-5" role="status">
        <div class="spinner-border pc-spinner" aria-hidden="true"></div>
        <p class="text-muted mt-3 mb-0">Chargement du calendrier…</p>
      </div>

      <template v-else>
        <!-- ===================== Prochaines fêtes ===================== -->
        <section class="mb-4" aria-labelledby="calendar-upcoming-title">
          <h2 id="calendar-upcoming-title" class="h5 mb-3">
            <i class="bi bi-hourglass-split me-1" aria-hidden="true"></i>
            Prochaines fêtes
          </h2>
          <div v-if="upcomingLoading" class="text-center py-3" role="status">
            <div class="spinner-border pc-spinner" aria-hidden="true"></div>
            <p class="text-muted small mt-2 mb-0">Chargement…</p>
          </div>
          <div v-else-if="!upcoming.length" class="alert alert-light" role="status">
            Aucun événement à venir.
          </div>
          <div v-else class="row g-3">
            <div
              v-for="event in upcoming"
              :key="event.id"
              class="col-12 col-md-6 col-lg-4"
            >
              <div class="card shadow-sm h-100 pc-event-card">
                <div class="card-body p-3">
                  <div class="d-flex justify-content-between align-items-start gap-2 mb-2">
                    <span class="badge pc-badge-days" :class="{ 'pc-badge-today': event.days_until === 0 }">
                      {{ daysUntilLabel(event.days_until) }}
                    </span>
                    <span class="badge" :class="typeBadgeClass(event.type)">
                      <i class="bi me-1" :class="typeIcon(event.type)" aria-hidden="true"></i>
                      {{ typeLabel(event.type) }}
                    </span>
                  </div>
                  <p class="text-muted small mb-1">
                    <i class="bi bi-calendar3 me-1" aria-hidden="true"></i>
                    {{ formatDate(event.date) }}
                  </p>
                  <h3 class="h6 mb-0">{{ event.name }}</h3>
                  <p v-if="event.name_ar" class="arabic-text pc-arabic-sm mb-2" lang="ar">
                    {{ event.name_ar }}
                  </p>
                  <p class="text-muted small mb-0">{{ event.description }}</p>
                </div>
              </div>
            </div>
          </div>
        </section>

        <!-- ===================== Calendrier de l'année ===================== -->
        <section aria-labelledby="calendar-year-title">
          <div class="d-flex flex-wrap align-items-center justify-content-between gap-2 mb-3">
            <h2 id="calendar-year-title" class="h5 mb-0">
              <i class="bi bi-calendar-week me-1" aria-hidden="true"></i>
              Calendrier {{ selectedYear }}
            </h2>
            <!-- Toggle Fêtes islamiques / nationales / Toutes -->
            <div class="btn-group" role="group" aria-label="Filtrer par type de fête">
              <button
                v-for="f in FILTERS"
                :key="f.value"
                type="button"
                class="btn btn-sm"
                :class="filter === f.value ? 'btn-pc-green' : 'btn-outline-pc'"
                :aria-pressed="filter === f.value"
                @click="filter = f.value"
              >
                {{ f.label }}
              </button>
            </div>
          </div>

          <div v-if="!filteredEvents.length" class="alert alert-light" role="status">
            Aucune fête ne correspond à ce filtre pour {{ selectedYear }}.
          </div>

          <div v-else class="card shadow-sm">
            <ul class="list-group list-group-flush">
              <li
                v-for="group in groupedByMonth"
                :key="group.key"
                class="list-group-item"
              >
                <p class="text-uppercase small fw-semibold pc-month-label mb-2">
                  {{ group.label }}
                </p>
                <div
                  v-for="event in group.events"
                  :key="event.id"
                  class="d-flex flex-wrap align-items-start gap-2 py-2 border-top"
                >
                  <div class="pc-event-date flex-shrink-0">
                    <i class="bi me-1" :class="typeIcon(event.type)" aria-hidden="true"></i>
                    {{ formatDate(event.date) }}
                  </div>
                  <div class="flex-grow-1">
                    <div class="d-flex flex-wrap align-items-center gap-2">
                      <span class="fw-semibold">{{ event.name }}</span>
                      <span class="badge" :class="typeBadgeClass(event.type)">
                        {{ typeLabel(event.type) }}
                      </span>
                    </div>
                    <div
                      v-if="event.hijri_date"
                      class="d-flex flex-wrap align-items-center gap-2 mt-1"
                    >
                      <span class="pc-hijri-date small">
                        <i class="bi bi-moon me-1" aria-hidden="true"></i>
                        {{ formatHijri(event.hijri_date) }}
                      </span>
                      <span
                        v-if="event.hijri_date.month_name_ar"
                        class="arabic-text pc-arabic-sm"
                        lang="ar"
                      >
                        {{ event.hijri_date.month_name_ar }}
                      </span>
                    </div>
                    <p class="text-muted small mb-0 mt-1">{{ event.description }}</p>
                  </div>
                </div>
              </li>
            </ul>
          </div>
        </section>
      </template>
    </div>
  </div>
</template>

<style scoped>
/* Spinner de chargement aux couleurs de la marque */
.pc-spinner {
  width: 2.5rem;
  height: 2.5rem;
  color: var(--pc-green);
}

/* Badge « fêtes islamiques » : vert de marque, texte blanc (AA) */
.pc-badge-islamic {
  background-color: var(--pc-green);
  color: #ffffff;
}

/* Badge « férié national » : rouge Maroc, texte blanc (AA) */
.pc-badge-national {
  background-color: #c1272d;
  color: #ffffff;
}

/* Badge année hégirienne : vert clair, texte vert sombre */
.pc-badge-hijri {
  background-color: rgba(20, 116, 111, 0.12);
  color: var(--pc-green-dark);
  font-weight: 600;
}

/* Badge « dans X jours » : fond neutre ; « aujourd'hui » en or assombri */
.pc-badge-days {
  background-color: rgba(20, 116, 111, 0.12);
  color: var(--pc-green-dark);
  font-weight: 600;
}

.pc-badge-today {
  background-color: var(--pc-gold-dark);
  color: #ffffff;
}

/* Mois en étiquette de groupe */
.pc-month-label {
  color: var(--pc-green);
  margin-bottom: 0.5rem;
}

/* Bouton « contour » de marque (cohérence avec les autres vues) */
.btn-outline-pc {
  color: var(--pc-green);
  border-color: var(--pc-green);
  background-color: #ffffff;
}

.btn-outline-pc:hover,
.btn-outline-pc:focus {
  background-color: var(--pc-green);
  color: #ffffff;
}

/* Date hégirienne mise en avant */
.pc-hijri-date {
  color: var(--pc-green-dark);
  font-weight: 600;
}

/* Texte arabe compact (noms de fêtes, mois) */
.pc-arabic-sm {
  font-size: 1.1rem;
  line-height: 1.7;
}

/* Colonne date de la liste annuelle */
.pc-event-date {
  min-width: 10rem;
  color: var(--pc-green-dark);
  font-weight: 600;
}
</style>
