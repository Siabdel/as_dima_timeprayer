<script setup>
// ===========================================================================
// TasbihCounter : compteur de dhikr local (aucune donnée envoyée au serveur).
// ---------------------------------------------------------------------------
// - Grand bouton rond central : TOUTE la zone est cliquable pour incrémenter ;
// - Cibles rapides (33, 100, 1000) + champ libre ; à l'atteinte de la cible :
//   animation + alerte Bootstrap « Cible atteinte ! » + remise à zéro proposée ;
// - Persistance localStorage (clé « pc_tasbih ») : compte, cible, dhikr choisi ;
// - Boutons réinitialiser et -1 (correction d'un dépassement) ;
// - Accessibilité : bouton natif (Enter/Espace gérés par le navigateur),
//   compte annoncé via aria-live="polite", libellé aria explicite.
// ===========================================================================
import { ref, computed, watch, onBeforeUnmount } from 'vue';

/** Clé de persistance locale. */
const STORAGE_KEY = 'pc_tasbih';

/** Dhikr proposés (liste fixe). */
const DHIKR_OPTIONS = [
  'SubhanAllah',
  'Alhamdulillah',
  'Allahu Akbar',
  'La ilaha illa Allah',
  'Astaghfirullah',
];

/** Cibles rapides. */
const QUICK_TARGETS = [33, 100, 1000];

// ---------------------------------------------------------------------------
// État local
// ---------------------------------------------------------------------------
const count = ref(0);
const target = ref(null); // null = aucune cible
const dhikr = ref(DHIKR_OPTIONS[0]);
/** Valeur du champ « cible personnalisée » (chaîne tant que non validée). */
const customTarget = ref('');
/** Alerte « cible atteinte » visible. */
const targetReached = ref(false);
/** Animation d'impulsion du bouton (retraitée après 700 ms). */
const pulseActive = ref(false);
let pulseTimeout = null;

// ---------------------------------------------------------------------------
// Persistance localStorage
// ---------------------------------------------------------------------------
/** Restaure l'état depuis le localStorage (valeurs invalides ignorées). */
function restorePersisted() {
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    if (!raw) return;
    const saved = JSON.parse(raw);
    if (Number.isFinite(saved?.count) && saved.count >= 0) {
      count.value = Math.floor(saved.count);
    }
    if (Number.isFinite(saved?.target) && saved.target >= 1) {
      target.value = Math.floor(saved.target);
    }
    if (DHIKR_OPTIONS.includes(saved?.dhikr)) {
      dhikr.value = saved.dhikr;
    }
  } catch {
    /* JSON invalide ou localStorage indisponible : état par défaut. */
  }
}

/** Persiste l'état courant (silencieux si localStorage indisponible). */
function persist() {
  try {
    window.localStorage.setItem(
      STORAGE_KEY,
      JSON.stringify({ count: count.value, target: target.value, dhikr: dhikr.value })
    );
  } catch {
    /* localStorage indisponible : on ignore. */
  }
}

restorePersisted();
watch([count, target, dhikr], persist);
onBeforeUnmount(() => {
  if (pulseTimeout) clearTimeout(pulseTimeout);
});

// ---------------------------------------------------------------------------
// Comptage
// ---------------------------------------------------------------------------
/** Texte annoncé aux lecteurs d'écran à chaque incrément/décrément. */
const announceText = computed(() => `${count.value} — ${dhikr.value}`);

/** Libellé accessible du grand bouton rond. */
const counterAria = computed(() =>
  target.value
    ? `Incrémenter le compteur : ${dhikr.value}, compte actuel ${count.value} sur une cible de ${target.value}`
    : `Incrémenter le compteur : ${dhikr.value}, compte actuel ${count.value}`
);

/** Progression « 12 / 33 » ou libellé libre. */
const progressLabel = computed(() =>
  target.value ? `${count.value} / ${target.value}` : `${count.value} comptés`
);

function pulse() {
  pulseActive.value = false;
  // Redémarre l'animation CSS même si une impulsion était déjà en cours.
  requestAnimationFrame(() => {
    pulseActive.value = true;
    if (pulseTimeout) clearTimeout(pulseTimeout);
    pulseTimeout = setTimeout(() => {
      pulseActive.value = false;
      pulseTimeout = null;
    }, 700);
  });
}

/** Incrémente (clic sur le bouton rond, Entrée ou Espace au clavier). */
function increment() {
  count.value += 1;
  if (target.value != null && count.value === target.value) {
    targetReached.value = true;
    pulse();
  }
}

/** Correction : retire un comptage (jamais en dessous de zéro). */
function decrement() {
  if (count.value === 0) return;
  count.value -= 1;
  if (target.value == null || count.value < target.value) {
    targetReached.value = false;
  }
}

/** Remise à zéro complète du compteur. */
function reset() {
  count.value = 0;
  targetReached.value = false;
}

// ---------------------------------------------------------------------------
// Cibles
// ---------------------------------------------------------------------------
/** Applique une cible rapide ; réévalue l'alerte si déjà atteinte. */
function setTarget(value) {
  target.value = value;
  targetReached.value = value != null && count.value >= value;
}

/** Champ libre : valide, borne (1 à 100 000) puis applique. */
function applyCustomTarget() {
  const parsed = Number.parseInt(customTarget.value, 10);
  if (Number.isFinite(parsed) && parsed >= 1) {
    setTarget(Math.min(parsed, 100000));
    customTarget.value = String(target.value);
  } else {
    // Valeur invalide : on réaffiche la cible courante.
    customTarget.value = target.value != null ? String(target.value) : '';
  }
}

/** Ferme l'alerte « cible atteinte » sans toucher au compteur. */
function dismissTargetReached() {
  targetReached.value = false;
}
</script>

<template>
  <div class="card shadow-sm h-100">
    <div class="card-body p-3 p-md-4">
      <!-- Choix du dhikr -->
      <div class="mb-3">
        <label for="pc-tasbih-dhikr" class="form-label small fw-semibold mb-1">
          Dhikr
        </label>
        <select
          id="pc-tasbih-dhikr"
          v-model="dhikr"
          class="form-select"
          aria-label="Choisir le dhikr à compter"
        >
          <option v-for="option in DHIKR_OPTIONS" :key="option" :value="option">
            {{ option }}
          </option>
        </select>
      </div>

      <!-- Alerte « cible atteinte » (annonce polie, non bloquante) -->
      <div v-if="targetReached" class="alert alert-success d-flex align-items-start gap-2 py-2 mb-3" role="status">
        <i class="bi bi-check-circle-fill mt-1" aria-hidden="true"></i>
        <div class="flex-grow-1">
          <strong>Cible atteinte !</strong>
          <span class="d-block small">
            {{ target }} {{ dhikr }} comptés. Qu'Allah accepte votre dhikr.
          </span>
          <button
            type="button"
            class="btn btn-success btn-sm mt-2"
            @click="reset"
          >
            <i class="bi bi-arrow-counterclockwise me-1" aria-hidden="true"></i>
            Remettre à zéro
          </button>
        </div>
        <button
          type="button"
          class="btn-close"
          aria-label="Fermer l'alerte de cible atteinte"
          @click="dismissTargetReached"
        ></button>
      </div>

      <!-- Grand compteur rond : bouton natif → Entrée et Espace incrémentent -->
      <div class="text-center my-3">
        <button
          type="button"
          class="pc-tasbih-button"
          :class="{ 'pc-tasbih-pulse': pulseActive }"
          :aria-label="counterAria"
          @click="increment"
        >
          <span class="pc-tasbih-count">{{ count }}</span>
          <span class="pc-tasbih-dhikr">{{ dhikr }}</span>
        </button>
        <!-- Le compte est annoncé aux lecteurs d'écran à chaque changement -->
        <span class="visually-hidden" aria-live="polite">{{ announceText }}</span>
        <p class="text-muted small mt-2 mb-0">{{ progressLabel }}</p>
      </div>

      <!-- Correction et remise à zéro -->
      <div class="d-flex justify-content-center gap-2 mb-3">
        <button
          type="button"
          class="btn btn-outline-pc"
          :disabled="count === 0"
          aria-label="Retirer un au compteur"
          @click="decrement"
        >
          <i class="bi bi-dash-lg me-1" aria-hidden="true"></i>
          −1
        </button>
        <button
          type="button"
          class="btn btn-outline-secondary"
          :disabled="count === 0"
          @click="reset"
        >
          <i class="bi bi-arrow-counterclockwise me-1" aria-hidden="true"></i>
          Réinitialiser
        </button>
      </div>

      <!-- Cibles rapides -->
      <fieldset class="mb-3">
        <legend class="form-label small fw-semibold mb-1">Cible</legend>
        <div class="d-flex flex-wrap gap-2">
          <button
            v-for="quick in QUICK_TARGETS"
            :key="quick"
            type="button"
            class="btn btn-outline-pc btn-sm"
            :class="{ active: target === quick }"
            :aria-pressed="target === quick"
            @click="setTarget(quick)"
          >
            {{ quick }}
          </button>
          <div class="pc-tasbih-custom">
            <label for="pc-tasbih-target" class="visually-hidden">
              Cible personnalisée
            </label>
            <input
              id="pc-tasbih-target"
              v-model="customTarget"
              type="number"
              inputmode="numeric"
              min="1"
              max="100000"
              class="form-control form-control-sm"
              placeholder="Cible libre"
              @change="applyCustomTarget"
            />
          </div>
        </div>
      </fieldset>

      <p class="text-muted small mb-0">
        <i class="bi bi-shield-check me-1" aria-hidden="true"></i>
        Votre compteur est enregistré uniquement sur cet appareil.
      </p>
    </div>
  </div>
</template>

<style scoped>
/* Grand bouton rond : toute la zone est cliquable */
.pc-tasbih-button {
  width: min(240px, 64vw);
  aspect-ratio: 1;
  border-radius: 50%;
  border: 4px solid var(--pc-gold);
  background-color: var(--pc-green);
  color: #ffffff;
  display: inline-flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 0.25rem;
  padding: 1rem;
  cursor: pointer;
  user-select: none;
  -webkit-tap-highlight-color: transparent;
  transition: background-color 0.15s ease, transform 0.1s ease;
}

.pc-tasbih-button:hover,
.pc-tasbih-button:focus {
  background-color: var(--pc-green-dark);
}

.pc-tasbih-button:active {
  transform: scale(0.97);
}

.pc-tasbih-count {
  font-size: clamp(2.75rem, 10vw, 4.5rem);
  font-weight: 700;
  line-height: 1;
  font-variant-numeric: tabular-nums;
}

.pc-tasbih-dhikr {
  font-size: 0.95rem;
  font-weight: 600;
  opacity: 0.92;
}

/* Impulsion à l'atteinte de la cible */
.pc-tasbih-pulse {
  animation: pc-tasbih-pulse 0.7s ease;
}

@keyframes pc-tasbih-pulse {
  0% {
    transform: scale(1);
  }
  35% {
    transform: scale(1.06);
  }
  70% {
    transform: scale(0.99);
  }
  100% {
    transform: scale(1);
  }
}

/* Champ « cible libre » compact, aligné avec les boutons rapides */
.pc-tasbih-custom {
  width: 9rem;
}

@media (prefers-reduced-motion: reduce) {
  .pc-tasbih-pulse {
    animation: none;
  }
}
</style>
