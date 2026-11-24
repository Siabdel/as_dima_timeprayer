<script setup>
// ===========================================================================
// ToolsView — page « Outils » (étape 6).
// ---------------------------------------------------------------------------
// Trois sections :
//   1. Qibla          → composant QiblaCompass (géolocalisation + GET /qibla/) ;
//   2. Date hégirienne → GET /hijri/ au montage (aujourd'hui, calendrier
//      Umm al-Qura), affichage français + nom arabe du mois + date grégorienne ;
//   3. Tasbih         → composant TasbihCounter (compteur local).
// États de chargement et d'erreur gérés (spinner + alerte Bootstrap).
// ===========================================================================
import { ref, computed, onMounted } from 'vue';
import { getHijri } from '../api/tools';
import QiblaCompass from '../components/QiblaCompass.vue';
import TasbihCounter from '../components/TasbihCounter.vue';

// ---------------------------------------------------------------------------
// Date hégirienne (aujourd'hui)
// ---------------------------------------------------------------------------
const hijriData = ref(null); // { day, year, month: { number, name, name_ar } }
const gregorianDate = ref(null); // « YYYY-MM-DD »
const hijriLoading = ref(true);
const hijriError = ref(null);

/** « 12 Jumada al-Akhira 1447 AH ». */
const hijriLabel = computed(() => {
  const hijri = hijriData.value;
  if (!hijri?.month?.name) return '';
  return `${hijri.day ?? ''} ${hijri.month.name} ${hijri.year ?? ''} AH`.trim();
});

/** Nom arabe du mois (رمضان). */
const hijriArabicMonth = computed(() => hijriData.value?.month?.name_ar ?? '');

/** Date grégorienne correspondante, en français (« 17 novembre 2026 »). */
const gregorianLabel = computed(() => {
  if (!gregorianDate.value) return '';
  try {
    return new Intl.DateTimeFormat('fr-FR', { dateStyle: 'long' }).format(
      new Date(`${gregorianDate.value}T00:00:00`)
    );
  } catch {
    return gregorianDate.value;
  }
});

onMounted(async () => {
  try {
    const response = await getHijri();
    hijriData.value = response.data?.hijri_date ?? null;
    gregorianDate.value = response.data?.gregorian_date ?? null;
  } catch (error) {
    hijriError.value =
      error?.response?.data?.error?.message ??
      "Impossible de récupérer la date hégirienne. Vérifiez votre connexion et réessayez.";
  } finally {
    hijriLoading.value = false;
  }
});
</script>

<template>
  <div class="row justify-content-center">
    <div class="col-12 col-lg-10 col-xl-9">
      <h1 class="h4 mb-4">Outils</h1>

      <div class="row g-4">
        <!-- ===================== Qibla ===================== -->
        <section class="col-12 col-lg-8" aria-labelledby="tools-qibla-title">
          <h2 id="tools-qibla-title" class="h5 mb-3">
            <i class="bi bi-compass me-1" aria-hidden="true"></i>
            Qibla
          </h2>
          <QiblaCompass />
        </section>

        <!-- ===================== Date hégirienne ===================== -->
        <section class="col-12 col-lg-4" aria-labelledby="tools-hijri-title">
          <h2 id="tools-hijri-title" class="h5 mb-3">
            <i class="bi bi-moon-stars me-1" aria-hidden="true"></i>
            Date hégirienne
          </h2>
          <div class="card shadow-sm h-100">
            <div class="card-body p-3 p-md-4 text-center">
              <!-- Chargement -->
              <div v-if="hijriLoading" class="py-4" role="status">
                <div class="spinner-border pc-tools-spinner" aria-hidden="true"></div>
                <p class="text-muted small mt-2 mb-0">Chargement de la date…</p>
              </div>

              <!-- Erreur -->
              <div v-else-if="hijriError" class="alert alert-danger py-2 mb-0" role="alert">
                <i class="bi bi-x-octagon me-1" aria-hidden="true"></i>
                {{ hijriError }}
              </div>

              <!-- Date du jour -->
              <template v-else-if="hijriLabel">
                <p class="h4 mb-1 pc-hijri-date" role="status" aria-live="polite">
                  {{ hijriLabel }}
                </p>
                <p v-if="hijriArabicMonth" class="arabic-text mb-2" lang="ar">
                  {{ hijriArabicMonth }}
                </p>
                <p class="text-muted small mb-0">
                  <i class="bi bi-calendar3 me-1" aria-hidden="true"></i>
                  {{ gregorianLabel }}
                </p>
              </template>
            </div>
          </div>
          <p class="text-muted small mt-2 mb-0">
            Calendrier Umm al-Qura, date du jour (UTC).
          </p>
        </section>

        <!-- ===================== Tasbih ===================== -->
        <section class="col-12" aria-labelledby="tools-tasbih-title">
          <h2 id="tools-tasbih-title" class="h5 mb-3">
            <i class="bi bi-record-circle me-1" aria-hidden="true"></i>
            Tasbih
          </h2>
          <div class="row justify-content-center">
            <div class="col-12 col-md-10 col-lg-8">
              <TasbihCounter />
            </div>
          </div>
        </section>
      </div>
    </div>
  </div>
</template>

<style scoped>
.pc-tools-spinner {
  width: 2rem;
  height: 2rem;
  color: var(--pc-green);
}

/* Date hégirienne mise en avant, couleur de marque */
.pc-hijri-date {
  color: var(--pc-green);
}
</style>
