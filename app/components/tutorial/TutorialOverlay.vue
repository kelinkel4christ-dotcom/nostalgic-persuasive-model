<script setup lang="ts">
import { useTutorialStore } from '~/stores/tutorial-store'

const tutorialStore = useTutorialStore()

const targetRect = ref<DOMRect | null>(null)
const tooltipPosition = ref({ top: 0, left: 0 })

function updateTargetPosition() {
  if (!tutorialStore.currentStep) return

  const targetEl = document.querySelector(tutorialStore.currentStep.targetSelector)
  if (targetEl) {
    targetRect.value = targetEl.getBoundingClientRect()
    calculateTooltipPosition()
    scrollToTarget(targetEl)
  }
}

function scrollToTarget(targetEl: Element) {
  if (!isElementInViewport(targetEl)) {
    targetEl.scrollIntoView({
      behavior: 'smooth',
      block: 'center',
    })
  }
}

function isElementInViewport(el: Element): boolean {
  const rect = el.getBoundingClientRect()
  return (
    rect.top >= 0 &&
    rect.left >= 0 &&
    rect.bottom <= window.innerHeight &&
    rect.right <= window.innerWidth
  )
}

function calculateTooltipPosition() {
  if (!targetRect.value || !tutorialStore.currentStep) return

  const rect = targetRect.value
  const tooltipWidth = 320
  const tooltipHeight = 180
  const gap = 12

  let top = 0
  let left = 0

  switch (tutorialStore.currentStep.position) {
    case 'top':
      top = rect.top - tooltipHeight - gap
      left = rect.left + (rect.width - tooltipWidth) / 2
      break
    case 'bottom':
      top = rect.bottom + gap
      left = rect.left + (rect.width - tooltipWidth) / 2
      break
    case 'left':
      top = rect.top + (rect.height - tooltipHeight) / 2
      left = rect.left - tooltipWidth - gap
      break
    case 'right':
      top = rect.top + (rect.height - tooltipHeight) / 2
      left = rect.right + gap
      break
    case 'center':
      top = (window.innerHeight - tooltipHeight) / 2
      left = (window.innerWidth - tooltipWidth) / 2
      break
  }

  left = Math.max(12, Math.min(left, window.innerWidth - tooltipWidth - 12))
  top = Math.max(12, Math.min(top, window.innerHeight - tooltipHeight - 12))

  tooltipPosition.value = { top, left }
}

function handleKeydown(e: KeyboardEvent) {
  if (e.key === 'Escape') {
    tutorialStore.skipTutorial()
  } else if (e.key === 'ArrowRight' || e.key === 'ArrowDown') {
    tutorialStore.nextStep()
  } else if (e.key === 'ArrowLeft' || e.key === 'ArrowUp') {
    tutorialStore.prevStep()
  }
}

function handleResize() {
  updateTargetPosition()
}

watch(
  () => tutorialStore.currentStepIndex,
  () => {
    nextTick(() => {
      updateTargetPosition()
    })
  }
)

onMounted(() => {
  updateTargetPosition()
  window.addEventListener('resize', handleResize)
  window.addEventListener('scroll', handleResize, true)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  window.removeEventListener('scroll', handleResize, true)
})

provide('updateTargetPosition', updateTargetPosition)
</script>

<template>
  <Teleport to="body">
    <div tabindex="-1" class="tutorial-overlay" @keydown="handleKeydown">
      <div class="tutorial-backdrop" />
      <div
        v-if="targetRect"
        class="tutorial-spotlight"
        :style="{
          top: `${targetRect.top - 4}px`,
          left: `${targetRect.left - 4}px`,
          width: `${targetRect.width + 8}px`,
          height: `${targetRect.height + 8}px`,
        }"
      />
      <TutorialTooltip
        v-if="tutorialStore.currentStep && targetRect"
        :step="tutorialStore.currentStep"
        :position="tooltipPosition"
        :is-last="tutorialStore.isLastStep"
        :progress="tutorialStore.progress"
      />
    </div>
  </Teleport>
</template>

<style scoped>
.tutorial-overlay {
  position: fixed;
  inset: 0;
  z-index: 9999;
  outline: none;
}

.tutorial-backdrop {
  position: absolute;
  inset: 0;
  background: rgba(0, 0, 0, 0.6);
  animation: fadeIn 0.3s ease-out;
}

.tutorial-spotlight {
  position: absolute;
  border-radius: 8px;
  box-shadow:
    0 0 0 9999px rgba(0, 0, 0, 0.6),
    0 0 24px rgba(59, 130, 246, 0.5);
  animation: pulse 2s ease-in-out infinite;
  pointer-events: none;
}

@keyframes fadeIn {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}

@keyframes pulse {
  0%,
  100% {
    box-shadow:
      0 0 0 9999px rgba(0, 0, 0, 0.6),
      0 0 24px rgba(59, 130, 246, 0.5);
  }
  50% {
    box-shadow:
      0 0 0 9999px rgba(0, 0, 0, 0.6),
      0 0 40px rgba(59, 130, 246, 0.8);
  }
}
</style>
