<script setup>
// ===========================================================================
// ShareAppCard : partager l'application par QR code, lien ou menu de partage
// du téléphone. Le QR (généré dans le navigateur, rien n'est envoyé) encode
// l'adresse du site : un ami le scanne et ouvre l'app, puis l'installe.
// ===========================================================================
import { ref, computed, onMounted } from 'vue';
import QRCode from 'qrcode';

const url = computed(() => window.location.origin + '/');
const qrDataUrl = ref('');
const copied = ref(false);
const canShare = typeof navigator !== 'undefined' && typeof navigator.share === 'function';
const message = "Assalamou alaykoum ! Voici l'application Prière & Coran : horaires de prière, Coran, météo.";

onMounted(async () => {
  try {
    qrDataUrl.value = await QRCode.toDataURL(url.value, {
      width: 480,
      margin: 2,
      errorCorrectionLevel: 'M',
      color: { dark: '#14746F', light: '#ffffff' },
    });
  } catch {
    qrDataUrl.value = '';
  }
});

async function share() {
  try {
    await navigator.share({ title: 'Prière & Coran', text: message, url: url.value });
  } catch {
    /* partage annulé */
  }
}

async function copy() {
  try {
    await navigator.clipboard.writeText(url.value);
    copied.value = true;
    setTimeout(() => (copied.value = false), 2000);
  } catch {
    window.prompt('Copiez ce lien :', url.value);
  }
}
</script>

<template>
  <div class="card shadow-sm mb-4">
    <div class="card-body p-4 text-center">
      <h2 class="h6 text-uppercase text-muted mb-3">
        <i class="bi bi-qr-code me-1" aria-hidden="true"></i>Partager l'application
      </h2>
      <img v-if="qrDataUrl" :src="qrDataUrl" alt="QR code : adresse de l'application" class="pc-qr mb-2" />
      <p class="text-muted small mb-3">
        Faites scanner ce code à un ami avec l'appareil photo de son téléphone, puis
        « Installer l'application » (Android) ou « Sur l'écran d'accueil » (iPhone, Safari).
      </p>
      <p class="fw-semibold mb-3 text-break">{{ url }}</p>
      <div class="d-flex flex-wrap justify-content-center gap-2">
        <button v-if="canShare" type="button" class="btn btn-pc-green" @click="share">
          <i class="bi bi-share me-1" aria-hidden="true"></i>Partager
        </button>
        <button type="button" class="btn btn-outline-pc" @click="copy">
          <i class="bi me-1" :class="copied ? 'bi-check2' : 'bi-clipboard'" aria-hidden="true"></i>
          {{ copied ? 'Lien copié' : 'Copier le lien' }}
        </button>
        <a v-if="qrDataUrl" class="btn btn-outline-secondary" :href="qrDataUrl" download="priere-et-coran-qr.png">
          <i class="bi bi-download me-1" aria-hidden="true"></i>Télécharger le QR
        </a>
      </div>
    </div>
  </div>
</template>

<style scoped>
.pc-qr {
  width: min(16rem, 70vw);
  height: auto;
  border: 1px solid rgba(20, 116, 111, 0.2);
  border-radius: 0.75rem;
}
</style>
