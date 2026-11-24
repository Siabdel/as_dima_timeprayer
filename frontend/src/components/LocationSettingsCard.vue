<script setup>
// ===========================================================================
// LocationSettingsCard : « Ma position » (Réglages).
// Lieu des horaires de prière et de la météo : géolocalisation (au clic
// uniquement) ou recherche manuelle ville + pays. Écrit dans le store
// prayerTimes (qui recharge les horaires et mémorise le lieu).
// ===========================================================================
import { ref, computed } from 'vue';
import { usePrayerTimesStore } from '../stores/prayerTimes';

const prayerStore = usePrayerTimesStore();

const city = ref('');
const country = ref('');
const geoLoading = ref(false);
const searching = ref(false);
const error = ref(null);
const done = ref(false);

const displayLocation = computed(() => {
  const loc = prayerStore.location;
  if (!loc) return '';
  if (loc.city) return loc.country ? `${loc.city}, ${loc.country}` : loc.city;
  return `Latitude ${Number(loc.latitude).toFixed(2)}, Longitude ${Number(loc.longitude).toFixed(2)}`;
});

async function apply(location) {
  error.value = null;
  done.value = false;
  try {
    await prayerStore.setLocation(location);
    done.value = true;
  } catch {
    error.value = "Impossible d'enregistrer ce lieu. Vérifiez la ville et réessayez.";
  }
}

function detect() {
  error.value = null;
  if (!('geolocation' in navigator)) {
    error.value = "La géolocalisation n'est pas disponible sur ce navigateur.";
    return;
  }
  geoLoading.value = true;
  navigator.geolocation.getCurrentPosition(
    async (pos) => {
      geoLoading.value = false;
      await apply({ latitude: pos.coords.latitude, longitude: pos.coords.longitude });
    },
    () => {
      geoLoading.value = false;
      error.value = 'Position refusée ou indisponible. Saisissez votre ville ci-dessous.';
    },
    { enableHighAccuracy: false, timeout: 10000, maximumAge: 300000 }
  );
}

async function search() {
  if (!city.value.trim()) return;
  searching.value = true;
  await apply({ city: city.value.trim(), country: country.value.trim() });
  searching.value = false;
}
</script>

<template>
  <div class="card shadow-sm mb-4">
    <div class="card-body p-4">
      <h2 class="h6 text-uppercase text-muted mb-3">
        <i class="bi bi-geo-alt me-1" aria-hidden="true"></i>Ma position
      </h2>
      <p class="mb-3">
        Lieu utilisé pour les horaires de prière et la météo :
        <span class="fw-semibold">{{ displayLocation || 'non défini' }}</span>
      </p>

      <button type="button" class="btn btn-pc-green mb-3" :disabled="geoLoading" @click="detect">
        <span v-if="geoLoading" class="spinner-border spinner-border-sm me-1" role="status" aria-hidden="true"></span>
        <i v-else class="bi bi-geo-alt me-1" aria-hidden="true"></i>
        Utiliser ma position
      </button>

      <form class="row g-2" @submit.prevent="search">
        <div class="col-12 col-md-5">
          <label for="pc-set-city" class="form-label small mb-1">Ville</label>
          <input id="pc-set-city" v-model="city" type="text" class="form-control" placeholder="Paris"
                 autocomplete="address-level2" />
        </div>
        <div class="col-12 col-md-4">
          <label for="pc-set-country" class="form-label small mb-1">Pays</label>
          <input id="pc-set-country" v-model="country" type="text" class="form-control"
                 placeholder="France" autocomplete="country-name" />
        </div>
        <div class="col-12 col-md-3 d-flex align-items-end">
          <button type="submit" class="btn btn-outline-pc w-100" :disabled="searching">
            <i class="bi bi-search me-1" aria-hidden="true"></i>Rechercher
          </button>
        </div>
      </form>

      <p v-if="error" class="text-danger small mt-2 mb-0" role="alert">{{ error }}</p>
      <p v-else-if="done" class="text-success small mt-2 mb-0" role="status">Lieu enregistré.</p>
    </div>
  </div>
</template>
