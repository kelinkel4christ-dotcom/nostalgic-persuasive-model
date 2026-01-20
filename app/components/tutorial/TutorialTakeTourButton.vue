<script setup lang="ts">
import { useTutorialStore } from '~/stores/tutorial-store'

const tutorialStore = useTutorialStore()

function handleClick() {
  tutorialStore.restartTour()
}
</script>

<template>
  <div class="take-tour-container">
    <UButton
      icon="i-lucide-sparkles"
      color="primary"
      size="lg"
      :ui="{ rounded: 'rounded-full' }"
      @click="handleClick"
    >
      Take Tour
    </UButton>
  </div>
</template>

<style scoped>
.take-tour-container {
  position: fixed;
  bottom: 24px;
  right: 24px;
  z-index: 100;
  animation: fadeInUp 0.4s ease-out;
}

@media (max-width: 640px) {
  .take-tour-container {
    bottom: 16px;
    right: 16px;
  }
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(16px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>
