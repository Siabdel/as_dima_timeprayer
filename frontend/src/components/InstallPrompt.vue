<script setup>
// Invitation à installer l'application (écran d'accueil du téléphone).
// Android / Chrome : bouton « Installer » (boîte native). iPhone : étapes Safari.
import { computed } from 'vue';
import { installState, installAvailable, promptInstall, dismissInstall } from '../services/pwaInstall';

const visible = computed(() => installAvailable() && !installState.dismissed);
const showIosSteps = computed(() => installState.isIos && !installState.canPrompt);

async function install() {
  const result = await promptInstall();
  if (result === 'dismissed') dismissInstall();
}
</script>

<template>
  <div v-if="visible" class="pc-install alert d-flex align-items-start gap-3 mb-3" role="region"
       aria-label="Installer l'application">
    <img src="/icons/icon-192.png" alt="" class="pc-install-icon" width="48" height="48" />
    <div class="flex-grow-1">
      <p class="fw-semibold mb-1">Installer Salawat sur votre téléphone</p>
      <p v-if="!showIosSteps" class="small mb-2">
        Accès direct depuis l'écran d'accueil, plein écran et rappels de prière.
      </p>
      <p v-else class="small mb-2">
        Dans Safari, touchez <i class="bi bi-box-arrow-up" aria-hidden="true"></i>
        <strong>Partager</strong>, puis <strong>« Sur l'écran d'accueil »</strong>.
      </p>
      <div class="d-flex gap-2">
        <button v-if="!showIosSteps" type="button" class="btn btn-sm btn-pc-green" @click="install">
          <i class="bi bi-download me-1" aria-hidden="true"></i>Installer
        </button>
        <button type="button" class="btn btn-sm btn-outline-secondary" @click="dismissInstall">
          Plus tard
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.pc-install {
  background: rgba(20, 116, 111, 0.1);
  border: 1px solid rgba(20, 116, 111, 0.3);
  color: #0e4f4b;
}
.pc-install-icon {
  border-radius: 12px;
  flex: 0 0 auto;
}
</style>
