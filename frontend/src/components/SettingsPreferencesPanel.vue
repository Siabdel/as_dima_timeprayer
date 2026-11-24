<script setup>
// ===========================================================================
// SettingsPreferencesPanel : réglages avancés (compte connecté).
//   A. Ma position  : fuseau horaire (auto / manuel), méthode de calcul par
//      organisme de référence, langue ;
//   B. Alertes & Adhan : mode d'alerte par prière, Adhan du Fajr, volume,
//      montée progressive, rappel avant l'Adhan ;
//   C. Audio & récitation : récitateur par défaut (aperçu, style), gestion
//      du cache audio.
// Les champs serveur passent par preferences.update() (PUT /auth/preferences/).
// ===========================================================================
import { ref, reactive, computed, onMounted } from 'vue';
import { usePreferencesStore } from '../stores/preferences';
import { useQuranPlayerStore } from '../stores/quranPlayer';
import { getAdhanSounds } from '../api/adhanSounds';
import { getChapterAudio } from '../api/quran';
import { playAdhanSound, stopAdhanSound, playBeep } from '../services/adhanAudio';
import {
  CALC_METHODS,
  COUNTRY_METHODS,
  COMMON_TIMEZONES,
  deviceTimezone,
  utcOffsetLabel,
  allTimezones,
} from '../utils/calcMethods';

const preferences = usePreferencesStore();
const player = useQuranPlayerStore();

const PRAYERS = [
  { key: 'fajr', label: 'Fajr' },
  { key: 'dhuhr', label: 'Dhuhr' },
  { key: 'asr', label: 'Asr' },
  { key: 'maghrib', label: 'Maghrib' },
  { key: 'isha', label: 'Isha' },
];
const ALERT_MODES = [
  { value: 'full', label: 'Sonnerie complète' },
  { value: 'beep', label: 'Bip court' },
  { value: 'vibrate', label: 'Vibreur' },
  { value: 'silent', label: 'Silencieux' },
];
const REMINDERS = [
  { value: 0, label: 'Aucun' },
  { value: 5, label: '5 minutes avant' },
  { value: 10, label: '10 minutes avant' },
  { value: 15, label: '15 minutes avant' },
  { value: 30, label: '30 minutes avant' },
];

// --- État du formulaire (miroir local des préférences serveur) ---------------
const form = reactive({
  timezone_mode: 'auto',
  timezone: '',
  language: 'fr',
  calculation_method: 3,
  alert_modes: {},
  reminder_minutes_before: 0,
  fajr_adhan_sound_id: null,
  adhan_volume: 100,
  adhan_fade_in: false,
});
const country = ref('');
const loaded = ref(false);
const saving = ref(false);
const saved = ref(false);
const error = ref(null);
let savedTimer = null;

function mirror(p) {
  if (!p) return;
  form.timezone_mode = p.timezone_mode ?? 'auto';
  form.timezone = p.timezone ?? '';
  form.language = p.language ?? 'fr';
  form.calculation_method = p.calculation_method ?? 3;
  form.alert_modes = { ...(p.alert_modes ?? {}) };
  form.reminder_minutes_before = p.reminder_minutes_before ?? 0;
  form.fajr_adhan_sound_id = p.fajr_adhan_sound_id ?? null;
  form.adhan_volume = p.adhan_volume ?? 100;
  form.adhan_fade_in = p.adhan_fade_in === true;
}

/** Enregistre un sous-ensemble de champs (fusionné avec les préférences). */
async function save(partial = {}) {
  Object.assign(form, partial);
  saving.value = true;
  error.value = null;
  saved.value = false;
  try {
    const { id, ...stored } = preferences.preference ?? {};
    const payload = { ...stored, ...form };
    // Mode auto : le fuseau enregistré est celui de l'appareil.
    if (form.timezone_mode === 'auto') payload.timezone = deviceTimezone();
    mirror(await preferences.update(payload));
    saved.value = true;
    clearTimeout(savedTimer);
    savedTimer = setTimeout(() => (saved.value = false), 2500);
  } catch (e) {
    error.value =
      e?.response?.data?.error?.message ??
      "Impossible d'enregistrer ces réglages. Réessayez.";
    mirror(preferences.preference);
  } finally {
    saving.value = false;
  }
}

// --- A. Ma position ------------------------------------------------------------
const device = deviceTimezone();
const deviceOffset = computed(() => utcOffsetLabel(device));
const zonesRest = computed(() =>
  allTimezones().filter((z) => !COMMON_TIMEZONES.includes(z))
);
const manualOffset = computed(() =>
  form.timezone ? utcOffsetLabel(form.timezone) : ''
);
const suggestedMethod = computed(
  () => COUNTRY_METHODS.find((c) => c.code === country.value)?.method ?? null
);
function applySuggestedMethod() {
  if (suggestedMethod.value !== null) save({ calculation_method: suggestedMethod.value });
}

// --- B. Alertes & Adhan ----------------------------------------------------------
const adhanSounds = ref([]);
function alertModeOf(prayer) {
  return form.alert_modes[prayer] ?? 'full';
}
function setAlertMode(prayer, mode) {
  save({ alert_modes: { ...form.alert_modes, [prayer]: mode } });
}
const testing = ref(false);
function testAlert() {
  if (testing.value) {
    stopAdhanSound();
    testing.value = false;
    return;
  }
  const sound =
    adhanSounds.value.find((s) => s.id === form.fajr_adhan_sound_id) ??
    adhanSounds.value.find((s) => s.id === preferences.preference?.adhan_sound_id) ??
    adhanSounds.value[0];
  if (!sound) return;
  testing.value = true;
  playAdhanSound(sound.url, {
    volume: form.adhan_volume,
    fadeIn: form.adhan_fade_in,
  }).catch(() => (testing.value = false));
  setTimeout(() => (testing.value = false), 15000);
}
function testBeep() {
  playBeep(form.adhan_volume);
  if (navigator.vibrate) navigator.vibrate([400, 150, 400]);
}

// --- C. Récitateur & cache audio -------------------------------------------------
const reciters = ref([]);
const styleFilter = ref('all');
const styles = computed(() => [
  ...new Set(reciters.value.map((r) => r.style).filter(Boolean)),
]);
const shownReciters = computed(() =>
  styleFilter.value === 'all'
    ? reciters.value
    : reciters.value.filter((r) => r.style === styleFilter.value)
);
let previewAudio = null;
const previewingReciter = ref(null);
function stopReciterPreview() {
  if (previewAudio) {
    previewAudio.pause();
    previewAudio = null;
  }
  previewingReciter.value = null;
}
async function previewReciter(r) {
  if (previewingReciter.value === r.id) return stopReciterPreview();
  stopReciterPreview();
  previewingReciter.value = r.id;
  try {
    const { data } = await getChapterAudio(1, r.id); // Al-Fatiha
    if (previewingReciter.value !== r.id) return;
    previewAudio = new Audio(data.audio_url);
    previewAudio.addEventListener('ended', stopReciterPreview);
    previewAudio.addEventListener('error', stopReciterPreview);
    previewAudio.addEventListener('timeupdate', () => {
      if (previewAudio && previewAudio.currentTime > 15) stopReciterPreview();
    });
    await previewAudio.play();
  } catch {
    stopReciterPreview();
  }
}
function chooseReciter(id) {
  player.setReciter(id);
  if (player.audioUrl) player.reloadCurrent();
}

const AUDIO_CACHE = 'pc-audio-v1';
const cacheSupported = typeof caches !== 'undefined';
const cacheCount = ref(0);
const cacheBytes = ref(null);
const cacheBusy = ref(false);
async function refreshCache() {
  if (!cacheSupported) return;
  try {
    const cache = await caches.open(AUDIO_CACHE);
    cacheCount.value = (await cache.keys()).length;
    const est = await navigator.storage?.estimate?.();
    cacheBytes.value = est?.usage ?? null;
  } catch {
    cacheCount.value = 0;
  }
}
async function clearCache() {
  cacheBusy.value = true;
  try {
    await caches.delete(AUDIO_CACHE);
  } finally {
    cacheBusy.value = false;
    await refreshCache();
  }
}
function formatBytes(n) {
  if (n == null) return '';
  return n > 1048576 ? `${(n / 1048576).toFixed(0)} Mo` : `${Math.round(n / 1024)} Ko`;
}

onMounted(async () => {
  try {
    mirror(preferences.preference ?? (await preferences.fetch()));
    loaded.value = Boolean(preferences.preference);
  } catch {
    loaded.value = false;
  }
  getAdhanSounds()
    .then((r) => (adhanSounds.value = r.data?.sounds ?? []))
    .catch(() => {});
  player.fetchReciters().then((list) => (reciters.value = list));
  refreshCache();
});
</script>

<template>
  <div>
    <p v-if="error" class="alert alert-danger py-2 small" role="alert">{{ error }}</p>
    <p class="small text-success mb-2" role="status" aria-live="polite">
      <span v-if="saved"><i class="bi bi-check-circle me-1" aria-hidden="true"></i>Enregistré</span>
    </p>

    <!-- ===================== A. Ma position ===================== -->
    <div class="card shadow-sm mb-4">
      <div class="card-body p-4">
        <h2 class="h6 text-uppercase text-muted mb-3">Fuseau horaire, calcul et langue</h2>

        <fieldset class="mb-3" :disabled="!loaded || saving">
          <legend class="form-label small fw-semibold">Fuseau horaire</legend>
          <div class="form-check">
            <input id="tz-auto" v-model="form.timezone_mode" class="form-check-input"
                   type="radio" value="auto" @change="save()" />
            <label class="form-check-label" for="tz-auto">
              Synchronisation automatique avec l'appareil
              <span class="text-muted small">— {{ device }} ({{ deviceOffset }})</span>
            </label>
          </div>
          <div class="form-check mb-2">
            <input id="tz-manual" v-model="form.timezone_mode" class="form-check-input"
                   type="radio" value="manual" @change="save()" />
            <label class="form-check-label" for="tz-manual">Sélection manuelle</label>
          </div>
          <select
            v-if="form.timezone_mode === 'manual'"
            v-model="form.timezone"
            class="form-select"
            aria-label="Fuseau horaire manuel"
            @change="save()"
          >
            <option value="" disabled>Choisir un fuseau…</option>
            <optgroup label="Courants">
              <option v-for="z in COMMON_TIMEZONES" :key="z" :value="z">
                {{ utcOffsetLabel(z) }} · {{ z }}
              </option>
            </optgroup>
            <optgroup label="Tous les fuseaux">
              <option v-for="z in zonesRest" :key="z" :value="z">
                {{ utcOffsetLabel(z) }} · {{ z }}
              </option>
            </optgroup>
          </select>
          <p v-if="form.timezone_mode === 'manual' && manualOffset" class="form-text mb-0">
            Décalage actuel : {{ manualOffset }}. L'heure d'été/hiver et le
            changement d'heure du Maroc pendant le Ramadan sont appliqués
            automatiquement.
          </p>
        </fieldset>

        <fieldset class="mb-3" :disabled="!loaded || saving">
          <legend class="form-label small fw-semibold">Méthode de calcul des prières</legend>
          <div class="row g-2 align-items-end">
            <div class="col-12 col-md-5">
              <label for="calc-country" class="form-label small mb-1">Mon pays</label>
              <select id="calc-country" v-model="country" class="form-select form-select-sm"
                      @change="applySuggestedMethod">
                <option value="">— Choisir —</option>
                <option v-for="c in COUNTRY_METHODS" :key="c.code" :value="c.code">{{ c.label }}</option>
              </select>
            </div>
            <div class="col-12 col-md-7">
              <label for="calc-method" class="form-label small mb-1">Organisme de référence</label>
              <select id="calc-method" v-model.number="form.calculation_method"
                      class="form-select form-select-sm" @change="save()">
                <option v-for="m in CALC_METHODS" :key="m.value" :value="m.value">{{ m.label }}</option>
              </select>
            </div>
          </div>
          <p class="form-text mb-0">
            Choisir un pays applique l'organisme recommandé ; vous pouvez ensuite le modifier.
          </p>
        </fieldset>

        <div :aria-disabled="!loaded">
          <label for="pref-language" class="form-label small fw-semibold">Langue</label>
          <select id="pref-language" v-model="form.language" class="form-select form-select-sm w-auto"
                  :disabled="!loaded || saving" @change="save()">
            <option value="fr">Français</option>
            <option value="en">English</option>
          </select>
          <p class="form-text mb-0">
            Détermine la traduction du Coran affichée par défaut. L'interface
            reste en français pour le moment.
          </p>
        </div>
      </div>
    </div>

    <!-- ===================== B. Alertes & Adhan ===================== -->
    <div class="card shadow-sm mb-4">
      <div class="card-body p-4">
        <h2 class="h6 text-uppercase text-muted mb-3">Alertes et Adhan avancé</h2>

        <fieldset :disabled="!loaded || saving" class="mb-3">
          <legend class="form-label small fw-semibold">Alerte par prière</legend>
          <div v-for="p in PRAYERS" :key="p.key"
               class="d-flex align-items-center justify-content-between gap-2 mb-2">
            <label :for="`alert-${p.key}`" class="mb-0">{{ p.label }}</label>
            <select :id="`alert-${p.key}`" class="form-select form-select-sm w-auto"
                    :value="alertModeOf(p.key)" @change="setAlertMode(p.key, $event.target.value)">
              <option v-for="m in ALERT_MODES" :key="m.value" :value="m.value">{{ m.label }}</option>
            </select>
          </div>
          <p class="form-text mb-0">
            Les rappels restent soumis à l'interrupteur de chaque prière
            (section Notifications). Le vibreur dépend de l'appareil.
          </p>
        </fieldset>

        <fieldset :disabled="!loaded || saving" class="mb-3">
          <label for="fajr-adhan" class="form-label small fw-semibold">
            Adhan spécifique du Fajr
            <span class="text-muted fw-normal">(« as-salâtu khayrun mina-n-nawm »)</span>
          </label>
          <select id="fajr-adhan" class="form-select form-select-sm"
                  :value="form.fajr_adhan_sound_id ?? ''"
                  @change="save({ fajr_adhan_sound_id: $event.target.value || null })">
            <option value="">Même Adhan que les autres prières</option>
            <option v-for="s in adhanSounds" :key="s.id" :value="s.id">
              {{ s.reciter }} — {{ s.name }}
            </option>
          </select>
        </fieldset>

        <fieldset :disabled="!loaded || saving" class="mb-3">
          <label for="adhan-volume" class="form-label small fw-semibold">
            Volume de l'Adhan : {{ form.adhan_volume }} %
          </label>
          <input id="adhan-volume" v-model.number="form.adhan_volume" type="range"
                 class="form-range" min="0" max="100" step="5" @change="save()" />
          <div class="form-check mt-2">
            <input id="adhan-fade" v-model="form.adhan_fade_in" class="form-check-input"
                   type="checkbox" @change="save()" />
            <label class="form-check-label" for="adhan-fade">Montée progressive du son (fade-in)</label>
          </div>
          <div class="d-flex gap-2 mt-2">
            <button type="button" class="btn btn-sm btn-outline-pc" @click="testAlert">
              <i class="bi" :class="testing ? 'bi-stop-fill' : 'bi-play-fill'" aria-hidden="true"></i>
              {{ testing ? 'Arrêter' : "Tester l'Adhan" }}
            </button>
            <button type="button" class="btn btn-sm btn-outline-secondary" @click="testBeep">
              Tester bip / vibreur
            </button>
          </div>
          <p class="form-text mb-0">
            Ce volume est propre à l'Adhan, indépendant du lecteur du Coran.
            Il s'applique quand l'application est ouverte.
          </p>
        </fieldset>

        <fieldset :disabled="!loaded || saving">
          <label for="reminder" class="form-label small fw-semibold">Rappel avant l'Adhan</label>
          <select id="reminder" v-model.number="form.reminder_minutes_before"
                  class="form-select form-select-sm w-auto" @change="save()">
            <option v-for="r in REMINDERS" :key="r.value" :value="r.value">{{ r.label }}</option>
          </select>
        </fieldset>
      </div>
    </div>

    <!-- ===================== C. Audio & récitation ===================== -->
    <div class="card shadow-sm mb-4">
      <div class="card-body p-4">
        <h2 class="h6 text-uppercase text-muted mb-3">Audio et récitation du Coran</h2>

        <div class="d-flex justify-content-between align-items-center mb-2">
          <span class="small fw-semibold">Récitateur par défaut</span>
          <select v-if="styles.length" v-model="styleFilter" class="form-select form-select-sm w-auto"
                  aria-label="Filtrer par style de récitation">
            <option value="all">Tous les styles</option>
            <option v-for="s in styles" :key="s" :value="s">{{ s }}</option>
          </select>
        </div>
        <div class="list-group list-group-flush mb-3 pc-reciter-list">
          <div v-for="r in shownReciters" :key="r.id"
               class="list-group-item px-0 d-flex align-items-center gap-3">
            <input :id="`reciter-${r.id}`" class="form-check-input flex-shrink-0" type="radio"
                   name="default-reciter" :checked="player.reciterId === r.id"
                   @change="chooseReciter(r.id)" />
            <label class="form-check-label flex-grow-1" :for="`reciter-${r.id}`">
              <span class="d-block fw-semibold">{{ r.name }}</span>
              <span v-if="r.style" class="d-block small text-muted">{{ r.style }}</span>
            </label>
            <button type="button" class="btn btn-sm"
                    :class="previewingReciter === r.id ? 'btn-outline-secondary' : 'btn-outline-pc'"
                    :aria-label="`Aperçu de ${r.name}`" @click="previewReciter(r)">
              <i class="bi" :class="previewingReciter === r.id ? 'bi-stop-fill' : 'bi-play-fill'"
                 aria-hidden="true"></i>
            </button>
          </div>
          <p v-if="!shownReciters.length" class="text-muted small mb-0">
            Liste des récitateurs indisponible pour le moment.
          </p>
        </div>

        <h3 class="h6 small text-uppercase text-muted mb-2">Stockage audio</h3>
        <p v-if="!cacheSupported" class="text-muted small mb-0">
          Le stockage hors ligne n'est pas disponible sur ce navigateur.
        </p>
        <template v-else>
          <p class="small mb-2">
            {{ cacheCount }} fichier(s) audio gardé(s) en cache pour l'écoute
            hors ligne et pour économiser vos données
            <span v-if="cacheBytes"> · stockage total de l'application : {{ formatBytes(cacheBytes) }}</span>.
            Les 40 plus récents sont conservés.
          </p>
          <button type="button" class="btn btn-sm btn-outline-danger"
                  :disabled="cacheBusy || cacheCount === 0" @click="clearCache">
            <i class="bi bi-trash me-1" aria-hidden="true"></i>
            Supprimer l'audio déjà écouté
          </button>
        </template>
      </div>
    </div>
  </div>
</template>

<style scoped>
.pc-reciter-list {
  max-height: 18rem;
  overflow-y: auto;
}
</style>
