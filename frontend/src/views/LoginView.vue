<script setup>
// Page de connexion : email + mot de passe, redirection après succès.
import { ref } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { useAuthStore } from '../stores/auth';

const route = useRoute();
const router = useRouter();
const auth = useAuthStore();

const email = ref('');
const password = ref('');
const submitting = ref(false);
const errorMessage = ref('');

// Connexion puis redirection vers la page demandée avant le garde du routeur,
// ou vers l'accueil par défaut.
async function handleSubmit() {
  submitting.value = true;
  errorMessage.value = '';
  try {
    await auth.login(email.value, password.value);
    const redirect = typeof route.query.redirect === 'string' ? route.query.redirect : '/';
    router.push(redirect);
  } catch (error) {
    // Format d'erreur global du backend : {"error": {"code", "message", "details"}}
    errorMessage.value =
      error?.response?.data?.error?.message ||
      'Connexion impossible. Vérifiez vos identifiants ou réessayez plus tard.';
  } finally {
    submitting.value = false;
  }
}
</script>

<template>
  <div class="row justify-content-center">
    <div class="col-12 col-md-8 col-lg-5">
      <div class="card shadow-sm">
        <div class="card-body p-4 p-md-5">
          <h1 class="h4 mb-1">Connexion</h1>
          <p class="text-muted small mb-4">
            Accédez à vos horaires de prière, rappels et réglages.
          </p>

          <!-- Message d'erreur dynamique, annoncé aux lecteurs d'écran -->
          <div v-if="errorMessage" class="alert alert-danger" role="alert" aria-live="polite">
            {{ errorMessage }}
          </div>

          <form novalidate @submit.prevent="handleSubmit">
            <div class="mb-3">
              <label class="form-label" for="login-email">Adresse e-mail</label>
              <input
                id="login-email"
                v-model="email"
                class="form-control"
                type="email"
                name="email"
                autocomplete="email"
                required
              />
            </div>

            <div class="mb-4">
              <label class="form-label" for="login-password">Mot de passe</label>
              <input
                id="login-password"
                v-model="password"
                class="form-control"
                type="password"
                name="password"
                autocomplete="current-password"
                required
              />
            </div>

            <button class="btn btn-pc-green w-100" type="submit" :disabled="submitting">
              <span
                v-if="submitting"
                class="spinner-border spinner-border-sm me-2"
                role="status"
                aria-hidden="true"
              ></span>
              {{ submitting ? 'Connexion…' : 'Se connecter' }}
            </button>
          </form>

          <p class="text-center text-muted small mt-3 mb-0">
            Pas encore de compte ?
            <router-link to="/register">Créer un compte</router-link>
          </p>
        </div>
      </div>
    </div>
  </div>
</template>
