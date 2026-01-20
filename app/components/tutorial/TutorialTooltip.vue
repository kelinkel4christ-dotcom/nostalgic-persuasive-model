<script setup lang="ts">
import type { TutorialStep } from '~/stores/tutorial-store'
import { useTutorialStore } from '~/stores/tutorial-store'

interface Props {
  step: TutorialStep
  position: { top: number; left: number }
  isLast: boolean
  progress: number
}

defineProps<Props>()
const tutorialStore = useTutorialStore()

function handleSkip() {
  tutorialStore.skipTutorial()
}

function handleNext() {
  tutorialStore.nextStep()
}

function handlePrev() {
  tutorialStore.prevStep()
}
</script>

<template>
  <div
    class="tutorial-tooltip fixed z-[10000] max-h-[65vh] w-[280px] overflow-y-auto rounded-xl border border-gray-200 bg-white shadow-xl sm:w-80 dark:border-gray-800 dark:bg-gray-900"
    :style="{
      top: `${position.top}px`,
      left: `${position.left}px`,
    }"
  >
    <div class="space-y-3 p-4">
      <div class="flex items-center justify-between">
        <span class="step-badge">Step {{ tutorialStore.currentStepIndex + 1 }} of 9</span>
        <button class="skip-button" @click="handleSkip">Skip</button>
      </div>

      <h3 class="text-base leading-tight font-semibold text-gray-900 dark:text-white">
        {{ step.title }}
      </h3>
      <p class="text-sm leading-relaxed text-gray-600 dark:text-gray-400">
        {{ step.description }}
      </p>

      <div class="flex items-center gap-3 pt-1">
        <UButton
          v-if="tutorialStore.currentStepIndex > 0"
          variant="ghost"
          size="xs"
          @click="handlePrev"
        >
          Back
        </UButton>
        <div class="h-1.5 flex-1 overflow-hidden rounded-full bg-gray-200 dark:bg-gray-700">
          <div
            class="h-full rounded-full bg-blue-500 transition-all duration-300"
            :style="{ width: `${progress}%` }"
          />
        </div>
        <UButton color="primary" size="xs" @click="handleNext">
          {{ isLast ? 'Finish' : 'Next' }}
        </UButton>
      </div>
    </div>
  </div>
</template>

<style scoped>
.step-badge {
  font-size: 11px;
  font-weight: 500;
  color: #6b7280;
  background: #f3f4f6;
  padding: 3px 6px;
  border-radius: 9999px;
}

.dark .step-badge {
  color: #9ca3af;
  background: #374151;
}

.skip-button {
  font-size: 11px;
  color: #6b7280;
  background: none;
  border: none;
  cursor: pointer;
  padding: 3px 6px;
  border-radius: 4px;
  transition: background 0.2s;
}

.skip-button:hover {
  background: #f3f4f6;
}

.dark .skip-button:hover {
  background: #374151;
}

.animate-slide-in {
  animation: slideIn 0.3s ease-out;
}

@keyframes slideIn {
  from {
    opacity: 0;
    transform: translateY(8px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>
