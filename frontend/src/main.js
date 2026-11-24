// Point d'entrée de l'application « Prière & Coran » (Vue 3 + Pinia + Vue Router).
import { createApp } from 'vue';
import { createPinia } from 'pinia';

// Styles : Bootstrap 5, icônes Bootstrap, puis notre thème Sass personnalisé.
import 'bootstrap/dist/css/bootstrap.min.css';
import 'bootstrap-icons/font/bootstrap-icons.css';
import './assets/styles/main.scss';

import App from './App.vue';
import router from './router';

// JavaScript de Bootstrap (collapse de la navbar, etc.) — bundle Popper inclus.
import 'bootstrap/dist/js/bootstrap.bundle.min.js';

const app = createApp(App);

// Pinia d'abord : le garde du routeur utilise le store « auth ».
app.use(createPinia());
app.use(router);

app.mount('#app');
