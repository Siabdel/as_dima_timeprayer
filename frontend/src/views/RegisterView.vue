<script setup>
// Page d'inscription : email, prénom, nom, mot de passe + confirmation.
// Les erreurs de validation du backend sont affichées champ par champ.
import { reactive, ref } from 'vue';
import { useRouter } from 'vue-router';
import { useAuthStore } from '../stores/auth';

const router = useRouter();
const auth = useAuthStore();

const form = reactive({
  email: '',
  first_name: '',
  last_name: '',
  password: '',
  password2: '',
});

const submitting = ref(false);
const globalError = ref('');
// Erreurs de validation par champ, ex. { email: '...', password: '...' }
const fieldErrors = reactive({});

const FIELD_KEYS = ['email', 'first_name', 'last_name', 'password', 'password2'];

// Remplit fieldErrors depuis error.details (ex. { email: ["..."] }) ;
// les erreurs non liées à un champ (non_field_errors, detail, ...) sont
// remontées comme message global.
function parseDetails(details) {
  Object.keys(fieldErrors).forEach((key) => delete fieldErrors[key]);
  if (!details || typeof details !== 'object') return;
  const extras = [];
  for (const [key, value] of Object.entries(details)) {
    const message = Array.isArray(value) ? value.join(' ') : String(value);
    if (FIELD_KEYS.includes(key)) {
      fieldErrors[key] = message;
    } else {
      extras.push(message);
    }
  }
  if (extras.length > 0) globalError.value = extras.join(' ');
}

// Inscription, puis connexion automatique, puis retour à l'accueil.
async function handleSubmit() {
  submitting.value = true;
  globalError.value = '';
  try {
    await auth.register({ ...form });
    router.push('/');
  } catch (error) {
    const data = error?.response?.data;
    if (data?.error?.details && Object.keys(data.error.details).length > 0) {
      // Erreurs de validation : une par champ.
      parseDetails(data.error.details);
    } else {
      globalError.value =
        data?.error?.message || 'Inscription impossible. Réessayez plus tard.';
    }
  } finally {
    submitting.value = false;
  }
}
</script>

<template>
  <div class="row justify-content-center">
    <div class="col-12 col-md-8 col-lg-6">
      <div class="card shadow-sm">
        <div class="card-body p-4 p-md-5">
          <h1 class="h4 mb-1">Créer un compte</h1>
          <p class="text-muted small mb-4">
            Gratuit, sans publicité — vos données restent les vôtres.
          </p>

          <!-- Message d'erreur global (hors validation de champs) -->
          <div v-if="globalError" class="alert alert-danger" role="alert" aria-live="polite">
            {{ globalError }}
          </div>

          <form novalidate @submit.prevent="handleSubmit">
            <div class="mb-3">
              <label class="form-label" for="register-email">Adresse e-mail</label>
              <input
                id="register-email"
                v-model="form.email"
                class="form-control"
                :class="{ 'is-invalid': fieldErrors.email }"
                type="email"
                name="email"
                autocomplete="email"
                required
                :aria-invalid="fieldErrors.email ? 'true' : undefined"
                :aria-describedby="fieldErrors.email ? 'register-email-error' : undefined"
              />
              <div id="register-email-error" class="invalid-feedback">
                {{ fieldErrors.email }}
              </div>
            </div>

            <div class="row">
              <div class="col-12 col-md-6 mb-3">
                <label class="form-label" for="register-first-name">Prénom</label>
                <input
                  id="register-first-name"
                  v-model="form.first_name"
                  class="form-control"
                  :class="{ 'is-invalid': fieldErrors.first_name }"
                  type="text"
                  name="given-name"
                  autocomplete="given-name"
                  :aria-invalid="fieldErrors.first_name ? 'true' : undefined"
                  :aria-describedby="fieldErrors.first_name ? 'register-first-name-error' : undefined"
                />
                <div id="register-first-name-error" class="invalid-feedback">
                  {{ fieldErrors.first_name }}
                </div>
              </div>

              <div class="col-12 col-md-6 mb-3">
                <label class="form-label" for="register-last-name">Nom</label>
                <input
                  id="register-last-name"
                  v-model="form.last_name"
                  class="form-control"
                  :class="{ 'is-invalid': fieldErrors.last_name }"
                  type="text"
                  name="family-name"
                  autocomplete="family-name"
                  :aria-invalid="fieldErrors.last_name ? 'true' : undefined"
                  :aria-describedby="fieldErrors.last_name ? 'register-last-name-error' : undefined"
                />
                <div id="register-last-name-error" class="invalid-feedback">
                  {{ fieldErrors.last_name }}
                </div>
              </div>
            </div>

            <div class="mb-3">
              <label class="form-label" for="register-password">Mot de passe</label>
              <input
                id="register-password"
                v-model="form.password"
                class="form-control"
                :class="{ 'is-invalid': fieldErrors.password }"
                type="password"
                name="new-password"
                autocomplete="new-password"
                required
                :aria-invalid="fieldErrors.password ? 'true' : undefined"
                :aria-describedby="fieldErrors.password ? 'register-password-error' : undefined"
              />
              <div id="register-password-error" class="invalid-feedback">
                {{ fieldErrors.password }}
              </div>
            </div>

            <div class="mb-4">
              <label class="form-label" for="register-password2">Confirmation du mot de passe</label>
              <input
                id="register-password2"
                v-model="form.password2"
                class="form-control"
                :class="{ 'is-invalid': fieldErrors.password2 }"
                type="password"
                name="new-password"
                autocomplete="new-password"
                required
                :aria-invalid="fieldErrors.password2 ? 'true' : undefined"
                :aria-describedby="fieldErrors.password2 ? 'register-password2-error' : undefined"
              />
              <div id="register-password2-error" class="invalid-feedback">
                {{ fieldErrors.password2 }}
              </div>
            </div>

            <button class="btn btn-pc-green w-100" type="submit" :disabled="submitting">
              <span
                v-if="submitting"
                class="spinner-border spinner-border-sm me-2"
                role="status"
                aria-hidden="true"
              ></span>
              {{ submitting ? 'Création…' : 'Créer mon compte' }}
            </button>
          </form>

          <p class="text-center text-muted small mt-3 mb-0">
            Déjà inscrit ?
            <router-link to="/login">Se connecter</router-link>
          </p>
        </div>
      </div>
    </div>
  </div>
</template>
