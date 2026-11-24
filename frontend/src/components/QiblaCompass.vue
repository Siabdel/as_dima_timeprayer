<script setup>
// ===========================================================================
// QiblaCompass : direction de la qibla depuis la position de l'utilisateur.
// ---------------------------------------------------------------------------
// - Géolocalisation demandée PAR LE CLIC uniquement (« Utiliser ma position ») ;
// - « Utiliser le dernier lieu connu » si des coordonnées existent déjà :
//   clé localStorage « pc_last_location » (écrite ici), puis lieu persisté
//   par la page Horaires (« pc_prayer_location », store prayerTimes), puis
//   lieu par défaut du compte (store preferences) ;
// - Appel GET /qibla/ (lat, lng) → cap en degrés, point cardinal, distance ;
// - Boussole SVG : l'aiguille est tournée de qibla_direction depuis le NORD
//   GÉOGRAPHIQUE (cap azimutal, pas d'utilisation du magnétomètre) ;
// - Accessibilité : résultat dans une zone aria-live="polite", erreurs
//   annoncées (role="alert"), focus visible hérité du thème.
// ===========================================================================
import { ref, computed, onMounted } from 'vue';
import { getQibla } from '../api/tools';
import { usePreferencesStore } from '../stores/preferences';

/** Clé du dernier lieu connu écrit par ce composant. */
const LAST_LOCATION_KEY = 'pc_last_location';
/** Clé historique du lieu écrit par la page « Horaires de prière ». */
const PRAYER_LOCATION_KEY = 'pc_prayer_location';

const preferencesStore = usePreferencesStore();

// ---------------------------------------------------------------------------
// État local
// ---------------------------------------------------------------------------
/** Coordonnées courantes { latitude, longitude } ou null. */
const coords = ref(null);
/** Réponse API : { qibla_direction, compass_point, kaaba_distance_km } */
const result = ref(null);
/** Chargements distincts : géolocalisation / requête API. */
const geoLoading = ref(false);
const apiLoading = ref(false);
/** Erreurs distinctes : géolocalisation / requête API. */
const geoError = ref(null);
const apiError = ref(null);
/** Dernier lieu connu disponible sans géolocalisation, ou null. */
const savedLocation = ref(null);

// ---------------------------------------------------------------------------
// Lecture / écriture du dernier lieu connu
// ---------------------------------------------------------------------------
/** Vrai si la valeur est un nombre fini (protection contre un localStorage corrompu). */
function isFiniteNumber(value) {
  return typeof value === 'number' && Number.isFinite(value);
}

/** Lit du JSON silencieusement (clé absente ou JSON invalide → null). */
function readJson(key) {
  try {
    const raw = window.localStorage.getItem(key);
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}

/**
 * Cherche un lieu réutilisable, par ordre de priorité :
 * 1. « pc_last_location » (ce composant) ;
 * 2. « pc_prayer_location » (store prayerTimes, page horaires) ;
 * 3. lieu par défaut du compte (store preferences, si déjà chargé).
 */
function findSavedLocation() {
  const candidates = [
    readJson(LAST_LOCATION_KEY),
    readJson(PRAYER_LOCATION_KEY)?.location ?? null,
    preferencesStore.preference?.default_location ?? null,
  ];
  for (const candidate of candidates) {
    if (candidate && isFiniteNumber(candidate.latitude) && isFiniteNumber(candidate.longitude)) {
      return { latitude: candidate.latitude, longitude: candidate.longitude };
    }
  }
  return null;
}

/** Persiste le dernier lieu connu (silencieux si localStorage indisponible). */
function saveLastLocation(latitude, longitude) {
  try {
    window.localStorage.setItem(
      LAST_LOCATION_KEY,
      JSON.stringify({ latitude, longitude, saved_at: new Date().toISOString() })
    );
  } catch {
    /* localStorage indisponible : on ignore. */
  }
}

/** Libellé lisible des coordonnées (séparateur décimal français). */
const coordsLabel = computed(() => {
  if (!coords.value) return '';
  const format = (value) =>
    value.toLocaleString('fr-FR', { maximumFractionDigits: 4 });
  return `Latitude ${format(coords.value.latitude)} · Longitude ${format(coords.value.longitude)}`;
});

// ---------------------------------------------------------------------------
// Géolocalisation
// ---------------------------------------------------------------------------
/** Message français correspondant à une erreur de géolocalisation. */
function geolocationErrorMessage(error) {
  switch (error?.code) {
    case 1: // PERMISSION_DENIED
      return "Accès à la position refusé. Autorisez la géolocalisation pour ce site dans les réglages de votre navigateur, ou choisissez votre ville depuis la page Horaires.";
    case 2: // POSITION_UNAVAILABLE
      return "Position indisponible actuellement. Vérifiez votre connexion et réessayez.";
    case 3: // TIMEOUT
      return "Délai dépassé lors de l'obtention de votre position. Réessayez.";
    default:
      return "Impossible d'obtenir votre position. Réessayez.";
  }
}

/** Géolocalisation : demandée UNIQUEMENT au clic sur le bouton. */
function useMyPosition() {
  geoError.value = null;
  if (!('geolocation' in navigator)) {
    geoError.value = "La géolocalisation n'est pas disponible sur ce navigateur.";
    return;
  }
  geoLoading.value = true;
  navigator.geolocation.getCurrentPosition(
    (position) => {
      geoLoading.value = false;
      const { latitude, longitude } = position.coords;
      coords.value = { latitude, longitude };
      saveLastLocation(latitude, longitude);
      savedLocation.value = findSavedLocation();
      fetchQibla(latitude, longitude);
    },
    (error) => {
      geoLoading.value = false;
      geoError.value = geolocationErrorMessage(error);
    },
    { enableHighAccuracy: false, timeout: 10000, maximumAge: 300000 }
  );
}

/** Utilise le dernier lieu connu (aucune demande de permission). */
function useSavedLocation() {
  geoError.value = null;
  const saved = savedLocation.value;
  if (!saved) return;
  coords.value = { latitude: saved.latitude, longitude: saved.longitude };
  fetchQibla(saved.latitude, saved.longitude);
}

// ---------------------------------------------------------------------------
// Appel API qibla
// ---------------------------------------------------------------------------
async function fetchQibla(latitude, longitude) {
  apiError.value = null;
  result.value = null;
  apiLoading.value = true;
  try {
    const response = await getQibla(latitude, longitude);
    result.value = response.data;
  } catch (error) {
    apiError.value =
      error?.response?.data?.error?.message ??
      "Impossible de calculer la direction de la qibla. Vérifiez votre connexion et réessayez.";
  } finally {
    apiLoading.value = false;
  }
}

// ---------------------------------------------------------------------------
// Formatage des résultats
// ---------------------------------------------------------------------------
/** Cap « 122,4° » (séparateur décimal français). */
const directionLabel = computed(() => {
  const direction = result.value?.qibla_direction;
  if (direction == null) return '';
  return `${direction.toLocaleString('fr-FR', {
    minimumFractionDigits: 1,
    maximumFractionDigits: 1,
  })}°`;
});

/** Distance « 4 123 km » (espacement insécable via Intl fr-FR). */
const distanceLabel = computed(() => {
  const distance = result.value?.kaaba_distance_km;
  if (distance == null) return '';
  return `${new Intl.NumberFormat('fr-FR', { maximumFractionDigits: 0 }).format(distance)} km`;
});

/** Libellé accessible de la boussole (role="img"). */
const compassAria = computed(() => {
  if (!result.value) return "Boussole : direction de la qibla non encore calculée";
  return `Boussole : qibla à ${directionLabel.value} depuis le nord géographique (${result.value.compass_point})`;
});

onMounted(() => {
  savedLocation.value = findSavedLocation();
});
</script>

<template>
  <div class="card shadow-sm h-100">
    <div class="card-body p-3 p-md-4">
      <!-- Actions -->
      <div class="d-flex flex-column flex-sm-row gap-2 mb-3">
        <button
          type="button"
          class="btn btn-pc-green"
          :disabled="geoLoading || apiLoading"
          @click="useMyPosition"
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
        <button
          v-if="savedLocation"
          type="button"
          class="btn btn-outline-pc"
          :disabled="geoLoading || apiLoading"
          @click="useSavedLocation"
        >
          <i class="bi bi-clock-history me-1" aria-hidden="true"></i>
          Utiliser le dernier lieu connu
        </button>
      </div>

      <!-- Erreur de géolocalisation -->
      <p v-if="geoError" class="text-danger small mb-3" role="alert">
        <i class="bi bi-exclamation-triangle me-1" aria-hidden="true"></i>
        {{ geoError }}
      </p>

      <!-- Erreur API -->
      <div v-if="apiError" class="alert alert-danger py-2 mb-3" role="alert">
        <i class="bi bi-x-octagon me-1" aria-hidden="true"></i>
        {{ apiError }}
      </div>

      <!-- Coordonnées obtenues -->
      <p v-if="coordsLabel" class="text-muted small mb-3">
        <i class="bi bi-pin-map me-1" aria-hidden="true"></i>
        {{ coordsLabel }}
      </p>

      <!-- Chargement de la requête API -->
      <div v-if="apiLoading" class="text-center py-4" role="status">
        <div class="spinner-border pc-compass-spinner" aria-hidden="true"></div>
        <p class="text-muted mt-2 mb-0 small">Calcul de la qibla…</p>
      </div>

      <!-- Résultat (annoncé aux lecteurs d'écran) -->
      <div v-else-if="result" aria-live="polite">
        <div class="text-center">
          <!-- Boussole SVG : aiguille tournée de qibla_direction (sens horaire
               depuis le nord, exactement comme un azimut sur une carte). -->
          <svg
            viewBox="0 0 200 200"
            class="pc-compass-svg"
            role="img"
            :aria-label="compassAria"
          >
            <circle cx="100" cy="100" r="90" class="pc-compass-ring" />
            <circle cx="100" cy="100" r="80" class="pc-compass-inner" />
            <!-- Gradations tous les 45° -->
            <g class="pc-compass-ticks">
              <line
                v-for="tick in 8"
                :key="tick"
                x1="100"
                y1="12"
                x2="100"
                :y2="tick === 1 ? 26 : 20"
                :transform="`rotate(${(tick - 1) * 45} 100 100)`"
              />
            </g>
            <!-- Points cardinaux fixes (le nord reste en haut) -->
            <text x="100" y="34" text-anchor="middle" class="pc-compass-n">N</text>
            <text x="172" y="105" text-anchor="middle" class="pc-compass-point">E</text>
            <text x="100" y="176" text-anchor="middle" class="pc-compass-point">S</text>
            <text x="28" y="105" text-anchor="middle" class="pc-compass-point">W</text>
            <!-- Aiguille de la qibla : 0° = nord (vers le haut), rotation horaire -->
            <g :transform="`rotate(${result.qibla_direction} 100 100)`">
              <rect x="95" y="42" width="10" height="62" rx="5" class="pc-compass-needle" />
              <polygon points="100,30 90,50 110,50" class="pc-compass-needle-tip" />
              <rect x="96" y="104" width="8" height="58" rx="4" class="pc-compass-needle-tail" />
              <circle cx="100" cy="100" r="7" class="pc-compass-hub" />
            </g>
          </svg>

          <!-- Chiffres clés -->
          <dl class="row justify-content-center mb-0 mt-3 pc-compass-stats">
            <div class="col-6 col-sm-4">
              <dt class="text-muted small fw-normal">Cap</dt>
              <dd class="h5 mb-0 fw-semibold">{{ directionLabel }}</dd>
            </div>
            <div class="col-6 col-sm-4">
              <dt class="text-muted small fw-normal">Direction</dt>
              <dd class="h5 mb-0 fw-semibold">{{ result.compass_point }}</dd>
            </div>
            <div class="col-12 col-sm-4">
              <dt class="text-muted small fw-normal">Distance à La Mecque</dt>
              <dd class="h5 mb-0 fw-semibold">{{ distanceLabel }}</dd>
            </div>
          </dl>
        </div>
      </div>

      <!-- Invite avant tout calcul -->
      <p v-else class="text-muted text-center small mb-0 mt-2">
        Activez la géolocalisation pour afficher la direction de la qibla.
      </p>

      <!-- Note explicative sur la référence du cap -->
      <p class="text-muted small mb-0 mt-3 pc-compass-note">
        <i class="bi bi-info-circle me-1" aria-hidden="true"></i>
        Le cap est indiqué depuis le nord géographique&nbsp;; utilisez une
        boussole pour orienter votre appareil.
      </p>
    </div>
  </div>
</template>

<style scoped>
/* Boussole : anneau vert de marque, fond blanc */
.pc-compass-svg {
  width: 220px;
  max-width: 100%;
  height: auto;
  display: block;
  margin: 0 auto;
}

.pc-compass-ring {
  fill: #ffffff;
  stroke: var(--pc-green);
  stroke-width: 4;
}

.pc-compass-inner {
  fill: rgba(20, 116, 111, 0.04);
  stroke: rgba(20, 116, 111, 0.25);
  stroke-width: 1;
}

.pc-compass-ticks line {
  stroke: rgba(20, 116, 111, 0.4);
  stroke-width: 2;
  stroke-linecap: round;
}

/* Nord en vert de marque, autres points en gris contrasté */
.pc-compass-n {
  fill: var(--pc-green);
  font-size: 1rem;
  font-weight: 700;
}

.pc-compass-point {
  fill: #5c6b6a;
  font-size: 0.9rem;
  font-weight: 600;
}

/* Aiguille : or (accent décoratif, texte large uniquement) */
.pc-compass-needle {
  fill: var(--pc-green);
}

.pc-compass-needle-tip {
  fill: var(--pc-gold);
  stroke: var(--pc-green);
  stroke-width: 1;
}

.pc-compass-needle-tail {
  fill: rgba(20, 116, 111, 0.25);
}

.pc-compass-hub {
  fill: #ffffff;
  stroke: var(--pc-green);
  stroke-width: 2;
}

.pc-compass-spinner {
  width: 2rem;
  height: 2rem;
  color: var(--pc-green);
}

.pc-compass-note {
  border-top: 1px solid rgba(20, 116, 111, 0.12);
  padding-top: 0.5rem;
}
</style>
