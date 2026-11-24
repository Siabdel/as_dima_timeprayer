<script setup>
// ===========================================================================
// PrayerTimesView — page « Horaires de prière » (étape 2).
// ---------------------------------------------------------------------------
// - Lieu : géolocalisation (demandée PAR LE CLIC uniquement) ou saisie
//   ville + pays manuelle ;
// - Méthode de calcul et madhhab : persistés dans le store (localStorage)
//   et, si l'utilisateur est connecté, synchronisés avec /auth/preferences/
//   (PUT non bloquant) ;
// - Date hégirienne, alerte « stale », compte à rebours, grille de cartes ;
// - Au montage : priorité au lieu par défaut du compte connecté, sinon
//   restauration depuis le localStorage, sinon écran d'accueil.
// ===========================================================================
import { ref, computed, onMounted, nextTick } from 'vue';
import { usePrayerTimesStore } from '../stores/prayerTimes';
import { useAuthStore } from '../stores/auth';
import { usePreferencesStore } from '../stores/preferences';
import { formatHijri } from '../utils/time';
import { CALC_METHODS } from '../utils/calcMethods';
import PrayerTimesCard from '../components/PrayerTimesCard.vue';
import CountdownTimer from '../components/CountdownTimer.vue';
import WeatherCard from '../components/WeatherCard.vue';

const prayerStore = usePrayerTimesStore();
const authStore = useAuthStore();
const preferencesStore = usePreferencesStore();

// ---------------------------------------------------------------------------
// État local de la vue
// ---------------------------------------------------------------------------
/** Clé de la prochaine prière, émise par le CountdownTimer. */
const nextPrayerKey = ref(null);
/** Champs de la recherche manuelle ville + pays. */
const manualCity = ref('');
const manualCountry = ref('');
/** Référence du champ ville (pour le focus clavier depuis l'accueil). */
const cityInput = ref(null);
/** Chargement de la géolocalisation + message d'erreur dédié. */
const geoLoading = ref(false);
const geoError = ref(null);
/** Formulaire ville/pays révélé sur l'écran d'accueil (aucun lieu défini). */
const showCityForm = ref(false);

// Méthodes de calcul proposées (contrat API : entier 0-30, défaut 3).
const METHODS = CALC_METHODS;

// ---------------------------------------------------------------------------
// Propriétés calculées
// ---------------------------------------------------------------------------
/** Vrai si un lieu est défini (coordonnées ou ville). */
const hasLocation = computed(() => Boolean(prayerStore.location));

/** Libellé lisible du lieu courant. */
const displayLocation = computed(() => {
  const loc = prayerStore.location;
  if (!loc) return '';
  if (loc.city) return loc.country ? `${loc.city}, ${loc.country}` : loc.city;
  const lat = Number(loc.latitude).toFixed(2);
  const lon = Number(loc.longitude).toFixed(2);
  return `Latitude ${lat}, Longitude ${lon}`;
});

/** Date hégirienne formatée (« 10 Joumada al-Oula 1446 »). */
const hijriLabel = computed(() => formatHijri(prayerStore.data?.hijri_date));

/** Message d'erreur à afficher (contrat : error.response.data.error.message). */
const errorMessage = computed(() => {
  const err = prayerStore.error;
  if (!err) return null;
  // Erreur métier normalisée par le store (ex. no_default_location).
  if (err.message && !err.response) return err.message;
  return (
    err.response?.data?.error?.message ??
    'Impossible de récupérer les horaires de prière. Vérifiez votre connexion et réessayez.'
  );
});

// ---------------------------------------------------------------------------
// Actions
// ---------------------------------------------------------------------------
/** Géolocalisation : demandée UNIQUEMENT au clic sur le bouton. */
function detectLocation() {
  geoError.value = null;
  if (!('geolocation' in navigator)) {
    geoError.value = 'La géolocalisation n\'est pas disponible sur ce navigateur.';
    return;
  }
  geoLoading.value = true;
  navigator.geolocation.getCurrentPosition(
    async (position) => {
      geoLoading.value = false;
      try {
        await prayerStore.setLocation({
          latitude: position.coords.latitude,
          longitude: position.coords.longitude,
        });
      } catch {
        // L'erreur API est déjà exposée par le store.
      }
    },
    () => {
      geoLoading.value = false;
      geoError.value =
        'Position refusée ou indisponible. Saisissez votre ville manuellement ci-dessous.';
    },
    { enableHighAccuracy: false, timeout: 10000, maximumAge: 300000 }
  );
}

/** Recherche manuelle ville + pays. */
async function searchCity() {
  geoError.value = null;
  if (!manualCity.value.trim()) return;
  try {
    await prayerStore.setLocation({
      city: manualCity.value.trim(),
      country: manualCountry.value.trim(),
    });
  } catch {
    // L'erreur API est déjà exposée par le store.
  }
}

/** Bouton « Saisir une ville » de l'accueil : révèle le formulaire puis focus. */
async function focusCityInput() {
  showCityForm.value = true;
  await nextTick();
  cityInput.value?.focus();
}

/** Recharge les horaires avec le lieu/method/madhhab courants. */
async function refetch() {
  try {
    await prayerStore.fetch({});
  } catch {
    // L'erreur API est déjà exposée par le store.
  }
}

/**
 * Changement de méthode ou de madhhab : recharge immédiatement les horaires,
 * puis synchronise les préférences du compte connecté (PUT non bloquant).
 */
function onMethodChange() {
  if (hasLocation.value) refetch();
  syncPreferences();
}

/** PUT /auth/preferences/ — silencieux, ne bloque jamais l'affichage. */
function syncPreferences() {
  if (!authStore.isAuthenticated) return;
  preferencesStore
    .update({
      calculation_method: prayerStore.method,
      madhhab: prayerStore.madhhab,
    })
    .catch(() => {
      // Échec silencieux : l'affichage ne dépend pas de cette sauvegarde.
    });
}

// ---------------------------------------------------------------------------
// Montage : restauration du lieu puis premier chargement
// ---------------------------------------------------------------------------
onMounted(async () => {
  // 1) Restaure method/madhhab/location depuis le localStorage (visiteurs).
  prayerStore.restorePersisted();

  // 2) Si connecté : les préférences du compte ont la priorité.
  if (authStore.isAuthenticated) {
    try {
      const pref = await preferencesStore.fetch();
      if (pref?.calculation_method != null) {
        prayerStore.method = pref.calculation_method;
      }
      if (pref?.madhhab === 'standard' || pref?.madhhab === 'hanafi') {
        prayerStore.madhhab = pref.madhhab;
      }
      // Lieu par défaut du compte : { latitude, longitude } ou { city, country }.
      const defaultLocation = pref?.default_location;
      if (defaultLocation && typeof defaultLocation === 'object') {
        await prayerStore.setLocation(defaultLocation);
        return;
      }
    } catch {
      // Préférences indisponibles : on continue avec le localStorage.
    }
  }

  // 3) Sinon : lieu restauré du localStorage → chargement direct.
  if (prayerStore.location) {
    await refetch();
  }
});
</script>

<template>
  <div class="row justify-content-center">
    <div class="col-12 col-lg-10 col-xl-8">
      <!-- ===================== Écran d'accueil (aucun lieu) ===================== -->
      <div v-if="!hasLocation && !prayerStore.loading" class="card shadow-sm">
        <div class="card-body p-4 p-md-5 text-center">
          <i class="bi bi-geo-alt pc-placeholder-icon" aria-hidden="true"></i>
          <h1 class="h4 mt-3 mb-2">Choisissez votre lieu</h1>
          <p class="text-muted mb-4">
            Pour afficher les horaires de prière, indiquez votre position ou votre ville.
          </p>
          <div class="d-flex flex-column flex-sm-row justify-content-center gap-2">
            <button
              type="button"
              class="btn btn-pc-green"
              :disabled="geoLoading"
              @click="detectLocation"
            >
              <span
                v-if="geoLoading"
                class="spinner-border spinner-border-sm me-1"
                role="status"
                aria-hidden="true"
              ></span>
              <i v-else class="bi bi-geo-alt me-1" aria-hidden="true"></i>
              Utiliser ma position
            </button>
            <button type="button" class="btn btn-outline-pc" @click="focusCityInput">
              <i class="bi bi-buildings me-1" aria-hidden="true"></i>
              Saisir une ville
            </button>
          </div>

          <!-- Formulaire ville/pays révélé au clic sur « Saisir une ville » :
               corrige le bug où le champ n'existait que sur la page principale. -->
          <form v-if="showCityForm" class="row g-2 mt-3 text-start" @submit.prevent="searchCity">
            <div class="col-12 col-md-6">
              <label for="pc-city" class="form-label">Ville</label>
              <input
                id="pc-city"
                ref="cityInput"
                v-model="manualCity"
                type="text"
                class="form-control"
                placeholder="Paris"
                autocomplete="address-level2"
              />
            </div>
            <div class="col-12 col-md-4">
              <label for="pc-country" class="form-label">Pays</label>
              <input
                id="pc-country"
                v-model="manualCountry"
                type="text"
                class="form-control"
                placeholder="France"
                autocomplete="country-name"
              />
            </div>
            <div class="col-12 col-md-2 d-flex align-items-end">
              <button type="submit" class="btn btn-pc-green w-100">
                <i class="bi bi-search me-1" aria-hidden="true"></i>
                Rechercher
              </button>
            </div>
          </form>

          <p v-if="geoError" class="text-danger small mt-3 mb-0" role="alert">
            {{ geoError }}
          </p>
        </div>
      </div>

      <!-- ===================== Page principale ===================== -->
      <div v-else>
        <!-- « Ma position » se gère dans les Réglages (ouverts à tous) -->
        <div class="d-flex flex-wrap align-items-center justify-content-between gap-2 mb-4">
          <span class="fw-semibold">
            <i class="bi bi-geo-alt me-1" aria-hidden="true"></i>{{ displayLocation }}
          </span>
          <router-link class="btn btn-outline-pc btn-sm" :to="{ name: 'settings' }">
            <i class="bi bi-gear me-1" aria-hidden="true"></i>Modifier ma position
          </router-link>
        </div>

        <!-- Sélecteurs méthode + madhhab -->
        <div class="card shadow-sm mb-4">
          <div class="card-body p-3 p-md-4">
            <h2 class="h5 mb-3">
              <i class="bi bi-sliders me-1" aria-hidden="true"></i>
              Calcul des horaires
            </h2>
            <div class="row g-3">
              <div class="col-12 col-md-6">
                <label for="pc-method" class="form-label">Méthode de calcul</label>
                <select
                  id="pc-method"
                  v-model.number="prayerStore.method"
                  class="form-select"
                  @change="onMethodChange"
                >
                  <option v-for="m in METHODS" :key="m.value" :value="m.value">
                    {{ m.label }}
                  </option>
                </select>
              </div>
              <div class="col-12 col-md-6">
                <label for="pc-madhhab" class="form-label">École juridique (Asr)</label>
                <select
                  id="pc-madhhab"
                  v-model="prayerStore.madhhab"
                  class="form-select"
                  @change="onMethodChange"
                >
                  <option value="standard">Standard (Shafi'i, Maliki, Hanbali)</option>
                  <option value="hanafi">Hanafi</option>
                </select>
              </div>
            </div>
            <p class="form-text text-muted mb-0 mt-2">
              Les préférences sont mémorisées sur cet appareil
              <template v-if="authStore.isAuthenticated"> et dans votre compte.</template>
            </p>
          </div>
        </div>

        <!-- Date hégirienne -->
        <div
          v-if="hijriLabel"
          class="pc-hijri-banner text-center mb-4"
          role="status"
        >
          <i class="bi bi-moon-stars me-2" aria-hidden="true"></i>
          <span>{{ hijriLabel }}</span>
          <span class="arabic-text d-block mt-1" lang="ar">
            {{ prayerStore.data?.hijri_date?.month?.name_ar ?? '' }}
          </span>
        </div>

        <!-- Alerte données en cache périmées -->
        <div v-if="prayerStore.data?.stale" class="alert alert-warning" role="status">
          <i class="bi bi-exclamation-triangle me-1" aria-hidden="true"></i>
          Données en cache (source momentanément indisponible)
        </div>

        <!-- Erreur de chargement (annoncée aux lecteurs d'écran) -->
        <div v-if="errorMessage" class="alert alert-danger" aria-live="polite" role="alert">
          <i class="bi bi-x-octagon me-1" aria-hidden="true"></i>
          {{ errorMessage }}
        </div>

        <!-- Chargement -->
        <div v-if="prayerStore.loading" class="text-center py-5" role="status">
          <div class="spinner-border pc-spinner" aria-hidden="true"></div>
          <p class="text-muted mt-3 mb-0">Chargement des horaires…</p>
        </div>

        <!-- Horaires + compte à rebours -->
        <template v-else-if="prayerStore.data">
          <CountdownTimer
            :timings="prayerStore.data"
            :timezone="prayerStore.data?.timezone"
            @next-prayer="nextPrayerKey = $event"
          />

          <h2 class="h5 mt-4 mb-3">Horaires du jour</h2>
          <PrayerTimesCard :timings="prayerStore.data" :next-prayer="nextPrayerKey" />

          <!-- Météo de la ville, sous les horaires -->
          <WeatherCard :location="prayerStore.location" />
        </template>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* Bandeau date hégirienne : fond vert, texte blanc AA */
.pc-hijri-banner {
  background-color: var(--pc-green);
  color: #ffffff;
  border-radius: 0.75rem;
  padding: 0.75rem 1rem;
  font-weight: 600;
}

.pc-spinner {
  width: 2.5rem;
  height: 2.5rem;
  color: var(--pc-green);
}

/* Bouton secondaire « contour » : vert de marque, AA sur fond blanc */
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

.btn-outline-pc:disabled {
  color: var(--pc-green);
  border-color: var(--pc-green);
  opacity: 0.8;
}
</style>
