<script setup>
// Page « Ramadan » (menu principal) : calendrier du mois sacré pour le lieu choisi.
import RamadanCalendar from '../components/RamadanCalendar.vue';
</script>

<template>
  <div class="row justify-content-center">
    <div class="col-12 col-lg-10 col-xl-9">
      <h1 class="h4 mb-1">Ramadan <span class="arabic-text" lang="ar">رمضان</span></h1>
      <p class="text-muted mb-3">
        Horaires de prière, Imsak, rupture du jeûne et dates importantes du mois sacré.
        <router-link :to="{ name: 'settings' }">Activer les rappels Imsak et rupture</router-link>
        dans les réglages.
      </p>
      <RamadanCalendar />
    </div>
  </div>
</template>
