<script setup>
// ===========================================================================
// CalcSettingsCard : « Calcul des horaires » (Réglages).
// Méthode de calcul (organisme de référence, suggestion par pays) et école
// juridique (Asr). Valeurs portées par le store prayerTimes (mémorisées sur
// l'appareil) et synchronisées avec le compte si connecté.
// ===========================================================================
import { ref, computed, onMounted } from 'vue';
import { usePrayerTimesStore } from '../stores/prayerTimes';
import { usePreferencesStore } from '../stores/preferences';
import { useAuthStore } from '../stores/auth';
import { CALC_METHODS, COUNTRY_METHODS } from '../utils/calcMethods';

const prayerStore = usePrayerTimesStore();
const preferences = usePreferencesStore();
const auth = useAuthStore();

const country = ref('');
const syncError = ref(false);

onMounted(async () => {
  prayerStore.restorePersisted();
  if (!auth.isAuthenticated) return;
  try {
    const pref = preferences.preference ?? (await preferences.fetch());
    if (pref?.calculation_method != null) prayerStore.method = pref.calculation_method;
    if (pref?.madhhab === 'standard' || pref?.madhhab === 'hanafi') {
      prayerStore.madhhab = pref.madhhab;
    }
  } catch {
    /* préférences du compte indisponibles : valeurs locales conservées */
  }
});

const suggested = computed(
  () => COUNTRY_METHODS.find((c) => c.code === country.value)?.method ?? null
);

/** Recharge les horaires, mémorise localement et synchronise le compte. */
async function onChange() {
  syncError.value = false;
  prayerStore.persistState();
  if (prayerStore.location) {
    try {
      await prayerStore.fetch({});
    } catch {
      /* l'erreur est exposée par le store (affichée sur l'accueil) */
    }
  }
  if (!auth.isAuthenticated) return;
  try {
    const { id, ...stored } = preferences.preference ?? {};
    await preferences.update({
      ...stored,
      calculation_method: prayerStore.method,
      madhhab: prayerStore.madhhab,
    });
  } catch {
    syncError.value = true;
  }
}

function applySuggestion() {
  if (suggested.value === null) return;
  prayerStore.method = suggested.value;
  onChange();
}
</script>

<template>
  <div class="card shadow-sm mb-4">
    <div class="card-body p-4">
      <h2 class="h6 text-uppercase text-muted mb-3">
        <i class="bi bi-sliders me-1" aria-hidden="true"></i>Calcul des horaires
      </h2>

      <div class="row g-3">
        <div class="col-12 col-md-5">
          <label for="calc-country" class="form-label small mb-1">Mon pays</label>
          <select id="calc-country" v-model="country" class="form-select" @change="applySuggestion">
            <option value="">— Choisir —</option>
            <option v-for="c in COUNTRY_METHODS" :key="c.code" :value="c.code">{{ c.label }}</option>
          </select>
        </div>
        <div class="col-12 col-md-7">
          <label for="pc-method" class="form-label small mb-1">Méthode de calcul (organisme de référence)</label>
          <select id="pc-method" v-model.number="prayerStore.method" class="form-select" @change="onChange">
            <option v-for="m in CALC_METHODS" :key="m.value" :value="m.value">{{ m.label }}</option>
          </select>
        </div>
        <div class="col-12">
          <label for="pc-madhhab" class="form-label small mb-1">École juridique (Asr)</label>
          <select id="pc-madhhab" v-model="prayerStore.madhhab" class="form-select" @change="onChange">
            <option value="standard">Standard (Shafi'i, Maliki, Hanbali)</option>
            <option value="hanafi">Hanafi</option>
          </select>
        </div>
      </div>

      <p class="form-text mb-0 mt-2">
        Choisir un pays applique l'organisme recommandé ; vous pouvez ensuite le modifier.
        Les réglages sont mémorisés sur cet appareil<template v-if="auth.isAuthenticated"> et dans votre compte</template>.
      </p>
      <p v-if="syncError" class="text-danger small mt-2 mb-0" role="alert">
        Enregistrement dans le compte impossible : réglage conservé sur cet appareil.
      </p>
    </div>
  </div>
</template>
