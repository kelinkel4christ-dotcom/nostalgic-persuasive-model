<script setup lang="ts">
import type { HabitType } from '~/components/onboarding/OnboardingHabitSelection.vue'
import type { ExperimentGroup } from '~/components/onboarding/OnboardingGroupSelection.vue'

definePageMeta({
  auth: true,
  layout: 'auth',
})

const toast = useToast()

// Step management
const currentStep = ref(0)
const isSubmitting = ref(false)

// Onboarding data
const experimentGroup = ref<ExperimentGroup | null>(null)
const birthYear = ref<number | null>(null)
const nostalgicPeriod = ref<{ start: number; end: number } | null>(null)
const habitType = ref<HabitType | null>(null)
const selectedContent = ref<{ movieIds: number[]; songIds: string[] } | null>(null)

// Dynamic steps based on group selection
const steps = computed(() => {
  if (experimentGroup.value === 'control') {
    // Control group: Group Selection -> Habit -> Consent (3 steps)
    return [
      { icon: 'i-lucide-flask-conical', label: 'Study Group' },
      { icon: 'i-lucide-target', label: 'Your Goal' },
      { icon: 'i-lucide-shield-check', label: 'Consent' },
    ]
  }
  // Treatment group: Group Selection -> Birth Year -> Habit -> Period -> Favorites -> Consent (6 steps)
  return [
    { icon: 'i-lucide-flask-conical', label: 'Study Group' },
    { icon: 'i-lucide-calendar-heart', label: 'Birth Year' },
    { icon: 'i-lucide-target', label: 'Your Goal' },
    { icon: 'i-lucide-sparkles', label: 'Nostalgic Era' },
    { icon: 'i-lucide-heart', label: 'Favorites' },
    { icon: 'i-lucide-shield-check', label: 'Consent' },
  ]
})

// Computed defaults for nostalgic period (used for content selection)
const activeNostalgicPeriod = computed(() => {
  if (nostalgicPeriod.value) return nostalgicPeriod.value
  if (!birthYear.value) return { start: 1990, end: 2005 }
  return {
    start: birthYear.value + 5,
    end: Math.min(birthYear.value + 19, new Date().getFullYear() - 1),
  }
})

// Step handlers
function handleGroupNext(group: ExperimentGroup) {
  experimentGroup.value = group
  currentStep.value = 1
}

function handleBirthYearNext(year: number) {
  birthYear.value = year
  currentStep.value = 2
}

function handleHabitNext(habit: HabitType) {
  habitType.value = habit
  if (experimentGroup.value === 'control') {
    // Control group skips to consent (step 2)
    currentStep.value = 2
  } else {
    // Treatment group goes to period selection (step 3)
    currentStep.value = 3
  }
}

function handlePeriodNext(period: { start: number; end: number }) {
  nostalgicPeriod.value = period
  currentStep.value = 4
}

function handlePeriodSkip() {
  nostalgicPeriod.value = null
  currentStep.value = 4
}

function handleContentNext(content: { movieIds: number[]; songIds: string[] }) {
  selectedContent.value = content
  currentStep.value = 5
}

async function handleComplete(consent: boolean) {
  if (!experimentGroup.value || !habitType.value) {
    toast.add({
      title: 'Missing data',
      description: 'Please complete all steps before finishing',
      color: 'error',
    })
    return
  }

  // Additional validation for treatment group
  if (experimentGroup.value === 'treatment') {
    if (!birthYear.value || !selectedContent.value) {
      toast.add({
        title: 'Missing data',
        description: 'Please complete all steps before finishing',
        color: 'error',
      })
      return
    }
  }

  isSubmitting.value = true

  try {
    // Build request body based on group
    const body =
      experimentGroup.value === 'treatment'
        ? {
            experimentGroup: 'treatment' as const,
            birthYear: birthYear.value!,
            habitType: habitType.value,
            nostalgicPeriodStart: activeNostalgicPeriod.value.start,
            nostalgicPeriodEnd: activeNostalgicPeriod.value.end,
            selectedMovieIds: selectedContent.value!.movieIds,
            selectedSongIds: selectedContent.value!.songIds,
            researchConsent: consent,
          }
        : {
            experimentGroup: 'control' as const,
            habitType: habitType.value,
            researchConsent: consent,
          }

    await $fetch('/api/onboarding/complete', {
      method: 'POST',
      body,
    })

    const message =
      experimentGroup.value === 'treatment'
        ? 'Your nostalgic journey begins now'
        : 'Your habit tracking journey begins now'

    toast.add({
      title: 'Welcome aboard! 🎉',
      description: message,
      color: 'success',
    })

    navigateTo('/')
  } catch (error) {
    console.error('Failed to complete onboarding:', error)
    toast.add({
      title: 'Something went wrong',
      description: 'Please try again',
      color: 'error',
    })
  } finally {
    isSubmitting.value = false
  }
}

function goBack() {
  if (currentStep.value > 0) {
    currentStep.value--
    // Reset group if going back to step 0
    if (currentStep.value === 0) {
      experimentGroup.value = null
    }
  }
}

// Determine which component to show based on step and group
const currentComponent = computed(() => {
  if (currentStep.value === 0) return 'group'

  if (experimentGroup.value === 'control') {
    // Control: 0=group, 1=habit, 2=consent
    if (currentStep.value === 1) return 'habit'
    if (currentStep.value === 2) return 'consent'
  } else {
    // Treatment: 0=group, 1=birthYear, 2=habit, 3=period, 4=content, 5=consent
    if (currentStep.value === 1) return 'birthYear'
    if (currentStep.value === 2) return 'habit'
    if (currentStep.value === 3) return 'period'
    if (currentStep.value === 4) return 'content'
    if (currentStep.value === 5) return 'consent'
  }

  return 'group'
})
</script>

<template>
  <div class="w-full">
    <!-- Progress Indicator -->
    <div class="mb-8">
      <div class="flex items-start justify-between">
        <template v-for="(step, index) in steps" :key="index">
          <!-- Step with Circle and Label -->
          <div class="flex flex-col items-center">
            <!-- Step Circle -->
            <div
              class="relative flex h-10 w-10 shrink-0 items-center justify-center rounded-full border-2 transition-all duration-300"
              :class="[
                index < currentStep
                  ? 'border-primary bg-primary text-white'
                  : index === currentStep
                    ? 'border-primary bg-primary/10 text-primary'
                    : 'border-gray-200 bg-white text-gray-400 dark:border-gray-700 dark:bg-gray-800',
              ]"
            >
              <UIcon v-if="index < currentStep" name="i-lucide-check" class="h-5 w-5" />
              <UIcon v-else :name="step.icon" class="h-5 w-5" />
            </div>

            <!-- Step Label (hidden on mobile) -->
            <span
              class="mt-2 hidden text-center text-xs font-medium transition-colors sm:block"
              :class="index <= currentStep ? 'text-primary' : 'text-gray-400 dark:text-gray-500'"
            >
              {{ step.label }}
            </span>
          </div>

          <!-- Connector Line -->
          <div
            v-if="index < steps.length - 1"
            class="mt-5 h-0.5 flex-1 transition-colors duration-300"
            :class="index < currentStep ? 'bg-primary' : 'bg-gray-200 dark:bg-gray-700'"
          />
        </template>
      </div>
    </div>

    <!-- Step Content -->
    <UCard class="overflow-visible">
      <div class="relative">
        <!-- Back Button -->
        <button
          v-if="currentStep > 0"
          class="absolute -top-2 -left-2 flex h-8 w-8 items-center justify-center rounded-full bg-gray-100 text-gray-600 transition-colors hover:bg-gray-200 dark:bg-gray-800 dark:text-gray-400 dark:hover:bg-gray-700"
          @click="goBack"
        >
          <UIcon name="i-lucide-arrow-left" class="h-4 w-4" />
        </button>

        <!-- Step Components -->
        <Transition name="slide-fade" mode="out-in">
          <OnboardingGroupSelection
            v-if="currentComponent === 'group'"
            key="step-group"
            @next="handleGroupNext"
          />
          <OnboardingBirthYear
            v-else-if="currentComponent === 'birthYear'"
            key="step-birthYear"
            @next="handleBirthYearNext"
          />
          <OnboardingHabitSelection
            v-else-if="currentComponent === 'habit'"
            key="step-habit"
            @next="handleHabitNext"
          />
          <OnboardingNostalgicPeriod
            v-else-if="currentComponent === 'period'"
            key="step-period"
            :birth-year="birthYear || 2000"
            @next="handlePeriodNext"
            @skip="handlePeriodSkip"
          />
          <OnboardingContentSelection
            v-else-if="currentComponent === 'content'"
            key="step-content"
            :period-start="activeNostalgicPeriod.start"
            :period-end="activeNostalgicPeriod.end"
            @next="handleContentNext"
          />
          <OnboardingResearchConsent
            v-else-if="currentComponent === 'consent'"
            key="step-consent"
            @complete="handleComplete"
          />
        </Transition>

        <!-- Loading Overlay -->
        <div
          v-if="isSubmitting"
          class="absolute inset-0 flex items-center justify-center rounded-lg bg-white/80 dark:bg-gray-900/80"
        >
          <div class="flex flex-col items-center gap-3">
            <UIcon name="i-lucide-loader-2" class="h-8 w-8 animate-spin text-primary" />
            <p class="text-sm font-medium text-gray-600 dark:text-gray-300">
              Saving your preferences...
            </p>
          </div>
        </div>
      </div>
    </UCard>
  </div>
</template>

<style scoped>
.slide-fade-enter-active,
.slide-fade-leave-active {
  transition: all 0.3s ease;
}

.slide-fade-enter-from {
  opacity: 0;
  transform: translateX(20px);
}

.slide-fade-leave-to {
  opacity: 0;
  transform: translateX(-20px);
}
</style>
