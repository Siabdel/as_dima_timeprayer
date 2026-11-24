<script setup>
// ===========================================================================
// LibraryView — page « Douâa & Hadiths » (route /library).
// ---------------------------------------------------------------------------
// - Onglets « Douâas » / « Hadiths » (nav-pills Bootstrap) ;
// - Filtre par catégorie (pills horizontales scrollables) ;
// - Cartes : douâa → titre, texte arabe RTL (police Amiri), translittération
//   italique, traduction FR, source en badge footer ; hadith → titre, texte
//   arabe RTL, traduction FR, narrateur + source en footer.
// Sources : GET /library/duas/, /library/hadiths/, /library/categories/.
// ===========================================================================
import { ref, computed, onMounted, watch } from 'vue';
import { getDuaCategories, getHadithCategories, getDuas, getHadiths } from '../api/library';

// ---------------------------------------------------------------------------
// État local de la vue
// ---------------------------------------------------------------------------
/** Onglet actif : « duas » | « hadiths ». */
const activeTab = ref('duas');

/** Catégories renvoyées par le backend (clé = key, libellé FR). */
const duaCategories = ref([]);
const hadithCategories = ref([]);

/** Liste courante d'entrées (douâas ou hadiths selon l'onglet). */
const items = ref([]);
/** Catégorie sélectionnée ('' = toutes). */
const selectedCategory = ref('');
const loading = ref(true);
const error = ref(null);

/** Catégories de l'onglet actif. */
const categories = computed(() =>
  activeTab.value === 'duas' ? duaCategories.value : hadithCategories.value
);

/** Libellé de la catégorie sélectionnée (badge compteur). */
const categoryLabel = computed(() => {
  const cat = categories.value.find((c) => c.key === selectedCategory.value);
  return cat?.label ?? 'Toutes';
});

// ---------------------------------------------------------------------------
// Chargement
// ---------------------------------------------------------------------------
/** Liste des entrées (douâas ou hadiths) avec le filtre courant. */
async function loadItems() {
  loading.value = true;
  error.value = null;
  const isDuas = activeTab.value === 'duas';
  try {
    const { data } = isDuas
      ? await getDuas(selectedCategory.value)
      : await getHadiths(selectedCategory.value);
    items.value = Array.isArray(data?.results) ? data.results : [];
  } catch {
    error.value =
      'Impossible de charger la bibliothèque. Vérifiez votre connexion et réessayez.';
    items.value = [];
  } finally {
    loading.value = false;
  }
}

/** Change d'onglet : réinitialise la catégorie et recharge. */
function switchTab(tab) {
  if (activeTab.value === tab) return;
  activeTab.value = tab;
  selectedCategory.value = '';
}

/** Changement de catégorie : recharge la liste. */
watch(selectedCategory, () => {
  loadItems();
});

watch(activeTab, () => {
  loadItems();
});

onMounted(async () => {
  // Catégories des deux onglets (endpoint public unique côté backend).
  try {
    const [duasCats, hadithsCats] = await Promise.all([
      getDuaCategories(),
      getHadithCategories(),
    ]);
    duaCategories.value = Array.isArray(duasCats.data?.duas) ? duasCats.data.duas : [];
    hadithCategories.value = Array.isArray(hadithsCats.data?.hadiths)
      ? hadithsCats.data.hadiths
      : [];
  } catch {
    // Sans catégories, le filtre n'est pas affiché : la liste reste accessible.
  }
  loadItems();
});
</script>

<template>
  <div class="row justify-content-center">
    <div class="col-12 col-lg-10 col-xl-9">
      <h1 class="h4 mb-1">Douâa &amp; Hadiths</h1>
      <p class="text-muted mb-4">
        Invocations et traditions du Prophète ﷺ, classées par thème.
      </p>

      <!-- ===================== Onglets Douâas / Hadiths ===================== -->
      <ul class="nav nav-pills mb-3" role="tablist">
        <li class="nav-item" role="presentation">
          <button
            type="button"
            class="nav-link"
            :class="{ active: activeTab === 'duas' }"
            :aria-selected="activeTab === 'duas'"
            role="tab"
            @click="switchTab('duas')"
          >
            <i class="bi bi-hands-praying me-1" aria-hidden="true"></i>
            Douâas
          </button>
        </li>
        <li class="nav-item" role="presentation">
          <button
            type="button"
            class="nav-link"
            :class="{ active: activeTab === 'hadiths' }"
            :aria-selected="activeTab === 'hadiths'"
            role="tab"
            @click="switchTab('hadiths')"
          >
            <i class="bi bi-book me-1" aria-hidden="true"></i>
            Hadiths
          </button>
        </li>
      </ul>

      <!-- ===================== Filtre par catégorie ===================== -->
      <div v-if="categories.length" class="pc-category-pills mb-4" role="group"
        aria-label="Filtrer par catégorie">
        <button
          type="button"
          class="btn btn-sm pc-pill"
          :class="selectedCategory === '' ? 'pc-pill-active' : 'btn-outline-pc'"
          :aria-pressed="selectedCategory === ''"
          @click="selectedCategory = ''"
        >
          Toutes
        </button>
        <button
          v-for="cat in categories"
          :key="cat.key"
          type="button"
          class="btn btn-sm pc-pill"
          :class="selectedCategory === cat.key ? 'pc-pill-active' : 'btn-outline-pc'"
          :aria-pressed="selectedCategory === cat.key"
          @click="selectedCategory = cat.key"
        >
          {{ cat.label }}
        </button>
      </div>

      <!-- Erreur de chargement -->
      <div v-if="error" class="alert alert-danger" aria-live="polite" role="alert">
        <i class="bi bi-x-octagon me-1" aria-hidden="true"></i>
        {{ error }}
        <button class="btn btn-outline-secondary btn-sm ms-2" type="button" @click="loadItems">
          Réessayer
        </button>
      </div>

      <!-- Chargement -->
      <div v-if="loading" class="text-center py-5" role="status">
        <div class="spinner-border pc-spinner" aria-hidden="true"></div>
        <p class="text-muted mt-3 mb-0">Chargement…</p>
      </div>

      <!-- Liste vide -->
      <div
        v-else-if="!items.length"
        class="alert alert-light"
        role="status"
      >
        Aucune entrée dans cette catégorie ({{ categoryLabel }}).
      </div>

      <!-- ===================== Cartes ===================== -->
      <div v-else class="row g-4">
        <!-- Douâas -->
        <template v-if="activeTab === 'duas'">
          <div v-for="dua in items" :key="dua.id" class="col-12 col-md-6 col-lg-6">
            <div class="card shadow-sm h-100 pc-library-card">
              <div class="card-body p-3 p-md-4">
                <h2 class="h6 mb-3">
                  <i class="bi bi-hands-praying me-1 pc-icon-green" aria-hidden="true"></i>
                  {{ dua.title }}
                </h2>
                <p v-if="dua.text_ar" class="arabic-text pc-arabic mb-2" lang="ar" dir="rtl">
                  {{ dua.text_ar }}
                </p>
                <p v-if="dua.transliteration" class="pc-transliteration mb-2">
                  {{ dua.transliteration }}
                </p>
                <p class="mb-0">{{ dua.translation_fr }}</p>
              </div>
              <div class="card-footer bg-transparent border-top-0 pt-0">
                <span class="badge pc-badge-source">
                  <i class="bi bi-bookmark me-1" aria-hidden="true"></i>
                  {{ dua.source }}
                </span>
              </div>
            </div>
          </div>
        </template>

        <!-- Hadiths -->
        <template v-else>
          <div v-for="hadith in items" :key="hadith.id" class="col-12 col-md-6 col-lg-6">
            <div class="card shadow-sm h-100 pc-library-card">
              <div class="card-body p-3 p-md-4">
                <h2 class="h6 mb-3">
                  <i class="bi bi-book me-1 pc-icon-green" aria-hidden="true"></i>
                  {{ hadith.title }}
                </h2>
                <p v-if="hadith.text_ar" class="arabic-text pc-arabic mb-2" lang="ar" dir="rtl">
                  {{ hadith.text_ar }}
                </p>
                <p class="mb-0">{{ hadith.translation_fr }}</p>
              </div>
              <div class="card-footer bg-transparent border-top-0 pt-0">
                <span class="badge pc-badge-source">
                  <i class="bi bi-person me-1" aria-hidden="true"></i>
                  {{ hadith.narrator }}
                </span>
                <span class="badge pc-badge-source ms-1">
                  <i class="bi bi-bookmark me-1" aria-hidden="true"></i>
                  {{ hadith.source }}
                </span>
              </div>
            </div>
          </div>
        </template>
      </div>
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

/* Onglets nav-pills : actif = vert de marque (Bootstrap suit --bs-primary) */
.nav-pills .nav-link {
  color: var(--pc-green);
}

.nav-pills .nav-link.active {
  background-color: var(--pc-green);
  color: #ffffff;
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

/* Pills de catégorie : défilement horizontal sur mobile */
.pc-category-pills {
  display: flex;
  flex-wrap: nowrap;
  gap: 0.5rem;
  overflow-x: auto;
  padding-bottom: 0.25rem;
  -webkit-overflow-scrolling: touch;
}

.pc-pill {
  white-space: nowrap;
  flex-shrink: 0;
}

.pc-pill-active {
  background-color: var(--pc-green);
  border-color: var(--pc-green);
  color: #ffffff;
}

/* Texte arabe : Amiri (fallback serif arabe), RTL */
.pc-arabic {
  font-size: 1.4rem;
  line-height: 2;
}

/* Translittération italique */
.pc-transliteration {
  font-style: italic;
  color: #5c6b6a;
}

/* Badge source / narrateur */
.pc-badge-source {
  background-color: rgba(20, 116, 111, 0.12);
  color: var(--pc-green-dark);
  font-weight: 600;
}

.pc-icon-green {
  color: var(--pc-green);
}
</style>
