<script setup>
// ===========================================================================
// SettingsView — page « Réglages » (réservée aux utilisateurs connectés).
// ---------------------------------------------------------------------------
// - Carte profil (inchangée) ;
// - Préférences de notification : toggles par prière + global, reliés au
//   store preferences (PUT /auth/preferences/ via preferences.update) ;
// - Notifications push : activation (permission + abonnement navigateur +
//   enregistrement backend via services/push), notification de test,
//   désactivation, état affiché depuis /notifications/status/ ET depuis
//   l'abonnement réel du navigateur ;
// - Déconnexion (inchangée).
// NOTE : la méthode de calcul, le madhhab et le lieu par défaut restent
// gérés depuis la page « Horaires de prière » (hors périmètre ici).
// ===========================================================================
import { ref, reactive, computed, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { useAuthStore } from '../stores/auth';
import { usePreferencesStore } from '../stores/preferences';
import { getSubscriptionStatus } from '../api/tools';
import { getAdhanSounds } from '../api/adhanSounds';
import { useReadingStatusStore } from '../stores/readingStatus';
import SettingsPreferencesPanel from '../components/SettingsPreferencesPanel.vue';
import LocationSettingsCard from '../components/LocationSettingsCard.vue';
import CalcSettingsCard from '../components/CalcSettingsCard.vue';
import ShareAppCard from '../components/ShareAppCard.vue';
import {
  isPushSupported,
  requestPermissionAndSubscribe,
  getExistingSubscription,
  unsubscribe,
  sendTest as sendTestPush,
} from '../services/push';
import {
  playAdhanSound,
  stopAdhanSound,
  setAdhanAudioStateListener,
} from '../services/adhanAudio';

const router = useRouter();
const auth = useAuthStore();
const preferences = usePreferencesStore();

/** Prières exposées par le backend (ordre chronologique). */
const PRAYERS = [
  { key: 'fajr', label: 'Fajr' },
  { key: 'sunrise', label: 'Lever du soleil' },
  { key: 'dhuhr', label: 'Dhuhr' },
  { key: 'asr', label: 'Asr' },
  { key: 'maghrib', label: 'Maghrib' },
  { key: 'isha', label: 'Isha' },
];

// ---------------------------------------------------------------------------
// Préférences de notification (toggles)
// ---------------------------------------------------------------------------
/** Miroir local des booléens de notification (édition instantanée). */
const notifForm = reactive({
  notifications_enabled: false,
  fajr: false,
  sunrise: false,
  dhuhr: false,
  asr: false,
  maghrib: false,
  isha: false,
  adhan_sound_id: null,
});

const notifLoaded = ref(false);
const notifSaving = ref(false);
const notifError = ref(null);
const notifSaved = ref(false);
let notifSavedTimeout = null;

/** Recopie un objet préférences serveur dans le miroir local. */
function mirrorPreferences(preference) {
  if (!preference) return;
  notifForm.notifications_enabled = preference.notifications_enabled === true;
  notifForm.adhan_sound_id = preference.adhan_sound_id ?? null;
  for (const prayer of PRAYERS) {
    notifForm[prayer.key] = preference[prayer.key] === true;
  }
}

/**
 * Payload d'enregistrement : les booléens de notification courant + les
 * autres champs tels que renvoyés par le serveur (PUT /auth/preferences/).
 */
function buildNotifPayload() {
  const stored = preferences.preference ?? {};
  const { id, ...passthrough } = stored; // « id » est en lecture seule
  return {
    ...passthrough,
    notifications_enabled: notifForm.notifications_enabled,
    ...Object.fromEntries(PRAYERS.map((p) => [p.key, notifForm[p.key]])),
    // Le son d'Adhan est une donnée locale (peut différer du serveur si
    // l'utilisateur vient de le changer) : toujours pris du miroir local.
    adhan_sound_id: notifForm.adhan_sound_id,
  };
}

/** Enregistre les toggles (PUT via le store) puis resynchronise l'affichage. */
async function saveNotifications() {
  notifSaving.value = true;
  notifError.value = null;
  notifSaved.value = false;
  try {
    const updated = await preferences.update(buildNotifPayload());
    mirrorPreferences(updated);
    notifSaved.value = true;
    if (notifSavedTimeout) clearTimeout(notifSavedTimeout);
    notifSavedTimeout = setTimeout(() => {
      notifSaved.value = false;
      notifSavedTimeout = null;
    }, 2500);
  } catch (error) {
    notifError.value =
      error?.response?.data?.error?.message ??
      error?.response?.data?.message ??
      "Impossible d'enregistrer vos préférences. Réessayez.";
    // Réaligne les interrupteurs sur l'état réel du serveur.
    try {
      mirrorPreferences(await preferences.fetch());
    } catch {
      mirrorPreferences(preferences.preference);
    }
  } finally {
    notifSaving.value = false;
  }
}

// ---------------------------------------------------------------------------
// Son de l'Adhan (catalogue + préférence + aperçu audio)
// ---------------------------------------------------------------------------
/** Catalogue des sons (GET /notifications/adhan-sounds/). */
const adhanSounds = ref([]);
const favorites = useReadingStatusStore();
/** Favoris au chargement : ordre figé pour ne pas déplacer les radios au clic. */
const favSnapshot = ref([]);
/** Catalogue trié : favoris (état au chargement) d'abord, ordre d'origine sinon. */
const sortedAdhanSounds = computed(() =>
  [...adhanSounds.value].sort(
    (a, b) =>
      Number(favSnapshot.value.includes(String(b.id))) -
      Number(favSnapshot.value.includes(String(a.id)))
  )
);
/** Son sélectionné (id) — miroir de notifForm.adhan_sound_id. */
const adhanSoundId = ref(null);
const adhanLoading = ref(false);
const adhanError = ref(null);
/** Id du son en cours d'écoute (aperçu) ou null. */
const previewingId = ref(null);

/** Charge le catalogue des sons et le choix courant de l'utilisateur. */
async function loadAdhanSounds() {
  adhanLoading.value = true;
  adhanError.value = null;
  try {
    const response = await getAdhanSounds();
    favSnapshot.value = [...favorites.favoriteReciters];
    adhanSounds.value = response.data?.sounds ?? [];
    const defaultValue = response.data?.default ?? null;
    // Choix courant : préférence sauvegardée, sinon défaut du catalogue.
    adhanSoundId.value = notifForm.adhan_sound_id ?? defaultValue;
  } catch {
    adhanError.value =
      "Impossible de charger les sons d'Adhan. Vérifiez votre connexion.";
  } finally {
    adhanLoading.value = false;
  }
}

/** Sélectionne un son : enregistre la préférence puis resynchronise. */
async function selectAdhanSound(soundId) {
  adhanSoundId.value = soundId;
  notifForm.adhan_sound_id = soundId;
  await saveNotifications();
}

/** Démarre/arrête l'aperçu d'un son (une seule lecture à la fois). */
function togglePreview(sound) {
  if (previewingId.value === sound.id) {
    stopAdhanSound();
    return;
  }
  playAdhanSound(sound.url)
    .then(() => {
      previewingId.value = sound.id;
    })
    .catch(() => {
      previewingId.value = null;
    });
}

// L'état de lecture (aperçu OU notification push) est partagé via
// services/adhanAudio : un « ended » ou un push remet l'icône à zéro.
setAdhanAudioStateListener((playing) => {
  if (!playing) previewingId.value = null;
});

// ---------------------------------------------------------------------------
// Notifications push (Web Push + backend)
// ---------------------------------------------------------------------------
/** Support navigateur évalué une seule fois (service worker + PushManager). */
const pushSupported = isPushSupported();

const statusLoading = ref(true);
/** État côté serveur : { subscribed, subscriptions_count, recent_notifications } */
const serverStatus = ref(null);
/** Abonnement réellement présent dans CE navigateur. */
const browserSubscribed = ref(false);
const pushBusy = ref(false);
const pushError = ref(null);
const pushMessage = ref(null);

const testPrayer = ref('fajr');
const testSending = ref(false);
/** { type: 'success' | 'warning' | 'danger', text } */
const testFeedback = ref(null);

/** Notifications considérées actives si le serveur OU le navigateur confirme. */
const pushActive = computed(
  () => Boolean(serverStatus.value?.subscribed) || browserSubscribed.value
);

/** Libellé du nombre d'appareils abonnés (info issue du serveur). */
const devicesLabel = computed(() => {
  const countValue = serverStatus.value?.subscriptions_count ?? 0;
  if (!countValue) return '';
  return countValue === 1
    ? '1 appareil abonné'
    : `${countValue} appareils abonnés`;
});

/** Dernières notifications réellement envoyées (5 max, pour information). */
const recentNotifications = computed(() =>
  (serverStatus.value?.recent_notifications ?? []).slice(0, 5)
);

/** Statut de log lisible (« sent » → « envoyée », sinon valeur brute). */
function logStatusLabel(value) {
  if (value === 'sent') return 'envoyée';
  return value;
}

/** Formate un instant ISO en français court (17/11 14:32). */
function formatSentAt(iso) {
  try {
    return new Intl.DateTimeFormat('fr-FR', {
      day: '2-digit',
      month: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
    }).format(new Date(iso));
  } catch {
    return iso;
  }
}

/** Actualise l'état : abonnement navigateur + état serveur. */
async function refreshPushState() {
  statusLoading.value = true;
  try {
    browserSubscribed.value = Boolean(await getExistingSubscription());
  } catch {
    browserSubscribed.value = false;
  }
  try {
    const response = await getSubscriptionStatus();
    serverStatus.value = response.data ?? null;
  } catch {
    // JWT expiré ou réseau indisponible : on garde l'état navigateur seul.
    serverStatus.value = null;
  } finally {
    statusLoading.value = false;
  }
}

/** Active les notifications : permission + abonnement + enregistrement. */
async function activatePush() {
  pushError.value = null;
  pushMessage.value = null;
  pushBusy.value = true;
  try {
    await requestPermissionAndSubscribe();
    pushMessage.value = 'Notifications activées sur cet appareil.';
    await refreshPushState();
  } catch (error) {
    pushError.value =
      error?.message ??
      "Impossible d'activer les notifications. Réessayez.";
  } finally {
    pushBusy.value = false;
  }
}

/** Désactive les notifications : backend puis navigateur. */
async function deactivatePush() {
  pushError.value = null;
  pushMessage.value = null;
  pushBusy.value = true;
  try {
    const outcome = await unsubscribe();
    if (outcome.error) {
      pushError.value =
        "La désinscription côté serveur a échoué. Cet appareil a bien été désabonné localement ; réessayez plus tard.";
    } else {
      pushMessage.value = 'Notifications désactivées sur cet appareil.';
    }
    await refreshPushState();
  } catch {
    pushError.value = "Impossible de désactiver les notifications. Réessayez.";
  } finally {
    pushBusy.value = false;
  }
}

/** Notification de test pour la prière choisie (throttle serveur : 5/h). */
async function onSendTest() {
  testFeedback.value = null;
  testSending.value = true;
  try {
    await sendTestPush(testPrayer.value);
    testFeedback.value = {
      type: 'success',
      text: 'Notification de test envoyée ! Vérifiez votre appareil.',
    };
  } catch (error) {
    const code = error?.response?.data?.error?.code;
    if (error?.response?.status === 400 && code === 'no_subscription') {
      testFeedback.value = {
        type: 'warning',
        text: "Aucun abonnement push enregistré. Activez d'abord les notifications sur cet appareil.",
      };
    } else if (error?.response?.status === 429) {
      testFeedback.value = {
        type: 'warning',
        text: 'Trop de tentatives : attendez un peu avant de renvoyer une notification de test.',
      };
    } else {
      testFeedback.value = {
        type: 'danger',
        text:
          error?.response?.data?.error?.message ??
          "L'envoi de la notification de test a échoué. Réessayez.",
      };
    }
  } finally {
    testSending.value = false;
  }
}

// ---------------------------------------------------------------------------
// Montage : profil, préférences, état push
// ---------------------------------------------------------------------------
onMounted(async () => {
  if (auth.isAuthenticated && !auth.user) {
    try {
      await auth.fetchMe();
    } catch {
      // Échec silencieux (token expiré, réseau...) — l'état reste affiché.
    }
  }
  if (auth.isAuthenticated) {
    try {
      const preference = await preferences.fetch();
      mirrorPreferences(preference);
    } catch {
      // Préférences indisponibles : les interrupteurs restent désactivés.
    }
    notifLoaded.value = Boolean(preferences.preference);
    try {
      await loadAdhanSounds();
    } catch {
      /* l'aperçu des sons est non bloquant */
    }
    try {
      await refreshPushState();
    } catch {
      statusLoading.value = false;
    }
  } else {
    notifLoaded.value = false;
    statusLoading.value = false;
  }
});

/** Charge l'état des interrupteurs ? (préférences disponibles) */
const canEditNotifications = computed(() => notifLoaded.value && !notifSaving.value);

// Déconnexion puis retour à la page de connexion.
function handleLogout() {
  auth.logout();
  router.push({ name: 'login' });
}
</script>

<template>
  <div class="row justify-content-center">
    <div class="col-12 col-md-10 col-lg-8">
      <h1 class="h4 mb-4">Réglages</h1>

      <!-- Ma position (lieu des horaires et de la météo) -->
      <LocationSettingsCard />

      <!-- Partager l'app : QR code, lien, menu de partage -->
      <ShareAppCard />

      <!-- Calcul des horaires (méthode + école juridique) -->
      <CalcSettingsCard />

      <!-- Invité : les réglages liés au compte demandent une connexion -->
      <div v-if="!auth.isAuthenticated" class="alert alert-info d-flex flex-wrap align-items-center justify-content-between gap-2" role="note">
        <span>
          <i class="bi bi-person me-1" aria-hidden="true"></i>
          Connectez-vous pour enregistrer vos préférences, recevoir les rappels
          d'Adhan et régler le calcul des horaires, le fuseau et la langue.
        </span>
        <router-link class="btn btn-sm btn-pc-green" :to="{ name: 'login', query: { redirect: '/settings' } }">
          Connexion
        </router-link>
      </div>

      <template v-if="auth.isAuthenticated">
      <!-- Carte profil -->
      <div class="card shadow-sm mb-4">
        <div class="card-body p-4">
          <h2 class="h6 text-uppercase text-muted mb-3">Profil</h2>
          <dl class="row mb-0">
            <dt class="col-sm-3">E-mail</dt>
            <dd class="col-sm-9 mb-2">{{ auth.user?.email || '—' }}</dd>

            <dt class="col-sm-3">Prénom</dt>
            <dd class="col-sm-9 mb-2">{{ auth.user?.first_name || '—' }}</dd>

            <dt class="col-sm-3">Nom</dt>
            <dd class="col-sm-9 mb-0">{{ auth.user?.last_name || '—' }}</dd>
          </dl>
        </div>
      </div>

      <!-- ===================== Préférences de notification ===================== -->
      <div class="card shadow-sm mb-4">
        <div class="card-body p-4">
          <div class="d-flex justify-content-between align-items-start gap-2 mb-3">
            <h2 class="h6 text-uppercase text-muted mb-0">
              Préférences de notification
            </h2>
            <span
              v-if="notifSaving"
              class="spinner-border spinner-border-sm text-secondary"
              role="status"
              aria-hidden="true"
            ></span>
            <span
              v-else-if="notifSaved"
              class="text-success small"
              role="status"
              aria-live="polite"
            >
              <i class="bi bi-check2 me-1" aria-hidden="true"></i>Enregistré
            </span>
          </div>

          <p v-if="notifError" class="alert alert-danger py-2 small" role="alert">
            <i class="bi bi-x-octagon me-1" aria-hidden="true"></i>
            {{ notifError }}
          </p>

          <!-- Chargement des préférences -->
          <div v-if="!notifLoaded" class="text-center py-3" role="status">
            <div class="spinner-border spinner-border-sm pc-settings-spinner" aria-hidden="true"></div>
            <p class="text-muted small mt-2 mb-0">Chargement des préférences…</p>
          </div>

          <template v-else>
            <!-- Interrupteur global -->
            <div class="form-check form-switch">
              <input
                id="pref-notif-enabled"
                v-model="notifForm.notifications_enabled"
                class="form-check-input"
                type="checkbox"
                role="switch"
                :disabled="!canEditNotifications"
                aria-describedby="pref-notif-enabled-help"
                @change="saveNotifications"
              />
              <label class="form-check-label" for="pref-notif-enabled">
                Activer les rappels de prière
              </label>
              <div id="pref-notif-enabled-help" class="form-text">
                Interrupteur général : désactivé, aucun rappel n'est envoyé.
              </div>
            </div>

            <!-- Interrupteurs par prière -->
            <fieldset class="mt-3 mb-0">
              <legend class="form-label small fw-semibold mb-2">Par prière</legend>
              <div class="row g-2">
                <div
                  v-for="prayer in PRAYERS"
                  :key="prayer.key"
                  class="col-6 col-md-4"
                >
                  <div class="form-check form-switch">
                    <input
                      :id="`pref-notif-${prayer.key}`"
                      v-model="notifForm[prayer.key]"
                      class="form-check-input"
                      type="checkbox"
                      role="switch"
                      :disabled="!canEditNotifications"
                      @change="saveNotifications"
                    />
                    <label class="form-check-label" :for="`pref-notif-${prayer.key}`">
                      {{ prayer.label }}
                    </label>
                  </div>
                </div>
              </div>
            </fieldset>
          </template>
        </div>
      </div>

      <!-- ===================== Son de l'Adhan ===================== -->
      <div class="card shadow-sm mb-4">
        <div class="card-body p-4">
          <div class="d-flex justify-content-between align-items-start gap-2 mb-3">
            <h2 class="h6 text-uppercase text-muted mb-0">Son de l'Adhan</h2>
            <span
              v-if="adhanLoading"
              class="spinner-border spinner-border-sm text-secondary"
              role="status"
              aria-hidden="true"
            ></span>
          </div>

          <p v-if="adhanError" class="alert alert-warning py-2 small mb-3" role="alert">
            <i class="bi bi-exclamation-triangle me-1" aria-hidden="true"></i>
            {{ adhanError }}
          </p>

          <p class="text-muted small mb-3">
            Récitation jouée avec les rappels de prière. Écoutez l'aperçu puis
            choisissez votre réciteur préféré.
          </p>

          <!-- Liste des sons du catalogue (radio + aperçu) -->
          <div class="list-group list-group-flush">
            <div
              v-for="sound in sortedAdhanSounds"
              :key="sound.id"
              class="list-group-item px-0 d-flex align-items-center gap-3"
            >
              <input
                :id="`adhan-sound-${sound.id}`"
                class="form-check-input flex-shrink-0"
                type="radio"
                name="adhan-sound"
                :value="sound.id"
                :checked="adhanSoundId === sound.id"
                :disabled="!canEditNotifications"
                @change="selectAdhanSound(sound.id)"
              />
              <label
                class="form-check-label flex-grow-1"
                :for="`adhan-sound-${sound.id}`"
              >
                <span class="d-block fw-semibold">
                  {{ sound.reciter }}
                  <span v-if="favorites.isFavoriteReciter(sound.id)" class="badge text-bg-warning ms-1">Favori</span>
                </span>
                <span class="d-block small text-muted">{{ sound.name }}</span>
              </label>
              <button
                type="button"
                class="btn btn-sm btn-link text-warning-emphasis"
                :aria-pressed="favorites.isFavoriteReciter(sound.id)"
                :aria-label="favorites.isFavoriteReciter(sound.id) ? `Retirer ${sound.reciter} des favoris` : `Ajouter ${sound.reciter} aux favoris`"
                @click="favorites.toggleFavoriteReciter(sound.id)"
              >
                <i
                  class="bi"
                  :class="favorites.isFavoriteReciter(sound.id) ? 'bi-star-fill' : 'bi-star'"
                  aria-hidden="true"
                ></i>
              </button>
              <button
                type="button"
                class="btn btn-sm"
                :class="previewingId === sound.id ? 'btn-outline-secondary' : 'btn-outline-pc'"
                :aria-label="previewingId === sound.id ? `Arrêter l'aperçu de ${sound.reciter}` : `Écouter l'aperçu de ${sound.reciter}`"
                @click="togglePreview(sound)"
              >
                <i
                  class="bi"
                  :class="previewingId === sound.id ? 'bi-stop-fill' : 'bi-play-fill'"
                  aria-hidden="true"
                ></i>
                {{ previewingId === sound.id ? 'Arrêter' : 'Écouter' }}
              </button>
            </div>
          </div>

          <p v-if="!adhanLoading && adhanSounds.length === 0" class="text-muted small mb-0">
            Aucun son disponible pour le moment.
          </p>
        </div>
      </div>

      <!-- Ma position, alertes avancées, audio & récitation -->
      </template>

      <!-- Fuseau/calcul/alertes (compte) + récitateur et cache audio (local) -->
      <SettingsPreferencesPanel :local-only="!auth.isAuthenticated" />

      <template v-if="auth.isAuthenticated">

      <!-- ===================== Notifications push ====================== -->
      <div class="card shadow-sm mb-4">
        <div class="card-body p-4">
          <div class="d-flex justify-content-between align-items-start gap-2 mb-3">
            <h2 class="h6 text-uppercase text-muted mb-0">Notifications push</h2>
            <span v-if="statusLoading" class="spinner-border spinner-border-sm text-secondary" role="status" aria-hidden="true"></span>
            <span
              v-else
              class="badge"
              :class="pushActive ? 'text-bg-success' : 'text-bg-secondary'"
              aria-live="polite"
            >
              {{ pushActive ? 'Actives' : 'Inactives' }}
            </span>
          </div>

          <!-- Navigateur sans support -->
          <div v-if="!pushSupported" class="alert alert-info mb-0" role="status">
            <i class="bi bi-info-circle me-1" aria-hidden="true"></i>
            Votre navigateur ne prend pas en charge les notifications push
            (service worker ou API Push absent, ou contexte non sécurisé).
            Les réglages de rappel restent enregistrés pour un appareil compatible.
          </div>

          <template v-else>
            <p v-if="pushError" class="alert alert-danger py-2 small mb-3" role="alert">
              <i class="bi bi-x-octagon me-1" aria-hidden="true"></i>
              {{ pushError }}
            </p>
            <p v-if="pushMessage" class="alert alert-success py-2 small mb-3" role="status">
              <i class="bi bi-check2-circle me-1" aria-hidden="true"></i>
              {{ pushMessage }}
            </p>

            <!-- État courant -->
            <p class="text-muted small mb-3">
              <i class="bi bi-phone me-1" aria-hidden="true"></i>
              <template v-if="devicesLabel">{{ devicesLabel }} sur ce compte.</template>
              <template v-else-if="browserSubscribed">
                Cet appareil est abonné, mais aucun abonnement n'est enregistré
                sur votre compte pour le moment.
              </template>
              <template v-else>Aucun abonnement push sur cet appareil.</template>
            </p>

            <!-- Activation / désactivation -->
            <div class="d-flex flex-column flex-sm-row gap-2 mb-4">
              <button
                v-if="!pushActive"
                type="button"
                class="btn btn-pc-green"
                :disabled="pushBusy"
                @click="activatePush"
              >
                <span
                  v-if="pushBusy"
                  class="spinner-border spinner-border-sm me-1"
                  role="status"
                  aria-hidden="true"
                ></span>
                <i v-else class="bi bi-bell me-1" aria-hidden="true"></i>
                Activer les notifications
              </button>
              <button
                v-else
                type="button"
                class="btn btn-outline-danger"
                :disabled="pushBusy"
                @click="deactivatePush"
              >
                <span
                  v-if="pushBusy"
                  class="spinner-border spinner-border-sm me-1"
                  role="status"
                  aria-hidden="true"
                ></span>
                <i v-else class="bi bi-bell-slash me-1" aria-hidden="true"></i>
                Désactiver
              </button>
            </div>

            <!-- Notification de test -->
            <div class="row g-2 align-items-end">
              <div class="col-12 col-sm-6 col-md-5">
                <label for="push-test-prayer" class="form-label small mb-1">
                  Prière pour le test
                </label>
                <select
                  id="push-test-prayer"
                  v-model="testPrayer"
                  class="form-select"
                  aria-label="Prière pour la notification de test"
                >
                  <option v-for="prayer in PRAYERS" :key="prayer.key" :value="prayer.key">
                    {{ prayer.label }}
                  </option>
                </select>
              </div>
              <div class="col-12 col-sm-6 col-md-7">
                <button
                  type="button"
                  class="btn btn-outline-pc w-100"
                  :disabled="testSending || !pushActive"
                  @click="onSendTest"
                >
                  <span
                    v-if="testSending"
                    class="spinner-border spinner-border-sm me-1"
                    role="status"
                    aria-hidden="true"
                  ></span>
                  <i v-else class="bi bi-send me-1" aria-hidden="true"></i>
                  Envoyer une notification de test
                </button>
              </div>
            </div>

            <p v-if="testFeedback" class="small mt-2 mb-0" :class="{
              'text-success': testFeedback.type === 'success',
              'text-warning-emphasis': testFeedback.type === 'warning',
              'text-danger': testFeedback.type === 'danger',
            }" role="status" aria-live="polite">
              {{ testFeedback.text }}
            </p>

            <!-- Dernières notifications envoyées (information) -->
            <div v-if="recentNotifications.length" class="mt-4">
              <h3 class="h6 small text-uppercase text-muted mb-2">
                Dernières notifications
              </h3>
              <ul class="list-group list-group-flush">
                <li
                  v-for="(item, index) in recentNotifications"
                  :key="index"
                  class="list-group-item px-0 py-2 d-flex justify-content-between align-items-center bg-transparent"
                >
                  <span class="text-capitalize">{{ item.prayer }}</span>
                  <span class="text-muted small">
                    {{ formatSentAt(item.sent_at) }}
                    <span class="badge text-bg-light border ms-1">
                      {{ logStatusLabel(item.status) }}
                    </span>
                  </span>
                </li>
              </ul>
            </div>
          </template>
        </div>
      </div>

      <!-- Déconnexion -->
      <div class="card shadow-sm">
        <div class="card-body p-4 d-flex justify-content-between align-items-center flex-wrap gap-2">
          <p class="mb-0 text-muted small">
            Vous pouvez vous déconnecter de cet appareil à tout moment.
          </p>
          <button class="btn btn-outline-danger" type="button" @click="handleLogout">
            <i class="bi bi-box-arrow-right me-1" aria-hidden="true"></i>
            Déconnexion
          </button>
        </div>
      </div>
      </template>
    </div>
  </div>
</template>

<style scoped>
/* Interrupteur de marque : vert PC quand actif */
.form-check-input:checked {
  background-color: var(--pc-green);
  border-color: var(--pc-green);
}

.pc-settings-spinner {
  color: var(--pc-green);
}
</style>
