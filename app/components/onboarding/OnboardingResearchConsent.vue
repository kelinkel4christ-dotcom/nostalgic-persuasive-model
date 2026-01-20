<script setup lang="ts">
const emit = defineEmits<{
  complete: [consent: boolean]
}>()

const consentChecked = ref(false)

function handleComplete() {
  emit('complete', consentChecked.value)
}
</script>

<template>
  <div class="space-y-8">
    <!-- Header -->
    <div class="text-center">
      <div
        class="mx-auto mb-6 flex h-20 w-20 items-center justify-center rounded-full bg-gradient-to-br from-cyan-500/20 to-blue-600/20"
      >
        <UIcon name="i-lucide-shield-check" class="h-10 w-10 text-cyan-500" />
      </div>
      <h2
        class="bg-gradient-to-r from-cyan-500 to-blue-600 bg-clip-text text-2xl font-bold text-transparent"
      >
        Research Participation
      </h2>
      <p class="mt-2 text-gray-500 dark:text-gray-400">
        Help us understand how nostalgia affects habit formation
      </p>
    </div>

    <!-- Consent Information -->
    <div class="space-y-4">
      <!-- Study Info Card -->
      <div
        class="rounded-xl border border-gray-200 bg-white p-5 dark:border-gray-700 dark:bg-gray-800/50"
      >
        <h3 class="mb-3 flex items-center gap-2 font-semibold text-gray-900 dark:text-white">
          <UIcon name="i-lucide-info" class="h-5 w-5 text-cyan-500" />
          About This Study
        </h3>
        <p class="text-sm leading-relaxed text-gray-600 dark:text-gray-300">
          This application is part of a research study exploring how nostalgic content can help
          people build positive habits. Your participation helps us understand the relationship
          between nostalgia and behavior change.
        </p>
      </div>

      <!-- Data Collection Card -->
      <div
        class="rounded-xl border border-gray-200 bg-white p-5 dark:border-gray-700 dark:bg-gray-800/50"
      >
        <h3 class="mb-3 flex items-center gap-2 font-semibold text-gray-900 dark:text-white">
          <UIcon name="i-lucide-database" class="h-5 w-5 text-cyan-500" />
          What We Collect
        </h3>
        <ul class="space-y-2 text-sm text-gray-600 dark:text-gray-300">
          <li class="flex items-start gap-2">
            <UIcon name="i-lucide-check-circle" class="mt-0.5 h-4 w-4 shrink-0 text-green-500" />
            Your content preferences (movies and music selections)
          </li>
          <li class="flex items-start gap-2">
            <UIcon name="i-lucide-check-circle" class="mt-0.5 h-4 w-4 shrink-0 text-green-500" />
            Your habit tracking progress and engagement patterns
          </li>
          <li class="flex items-start gap-2">
            <UIcon name="i-lucide-check-circle" class="mt-0.5 h-4 w-4 shrink-0 text-green-500" />
            Anonymized interaction data with the app
          </li>
        </ul>
      </div>

      <!-- Privacy Card -->
      <div
        class="rounded-xl border border-cyan-200 bg-gradient-to-r from-cyan-50 to-blue-50 p-5 dark:border-cyan-800/50 dark:from-cyan-900/20 dark:to-blue-900/20"
      >
        <h3 class="mb-3 flex items-center gap-2 font-semibold text-gray-900 dark:text-white">
          <UIcon name="i-lucide-lock" class="h-5 w-5 text-cyan-500" />
          Your Privacy
        </h3>
        <ul class="space-y-2 text-sm text-gray-600 dark:text-gray-300">
          <li class="flex items-start gap-2">
            <UIcon name="i-lucide-shield" class="mt-0.5 h-4 w-4 shrink-0 text-cyan-500" />
            All data is anonymized and stored securely
          </li>
          <li class="flex items-start gap-2">
            <UIcon name="i-lucide-shield" class="mt-0.5 h-4 w-4 shrink-0 text-cyan-500" />
            You can withdraw your consent at any time
          </li>
          <li class="flex items-start gap-2">
            <UIcon name="i-lucide-shield" class="mt-0.5 h-4 w-4 shrink-0 text-cyan-500" />
            Data is used solely for academic research
          </li>
        </ul>
      </div>
    </div>

    <!-- Consent Checkbox -->
    <div
      class="rounded-xl border-2 border-gray-200 bg-gray-50 p-4 transition-colors dark:border-gray-700 dark:bg-gray-800/30"
      :class="{
        'border-cyan-400 bg-cyan-50 dark:border-cyan-500 dark:bg-cyan-900/20': consentChecked,
      }"
    >
      <label class="flex cursor-pointer items-start gap-3">
        <UCheckbox v-model="consentChecked" class="mt-0.5" />
        <span class="text-sm text-gray-700 dark:text-gray-200">
          I agree to participate in this research study. I understand that my data will be collected
          and used for research purposes as described above, and that I can withdraw at any time.
        </span>
      </label>
    </div>

    <!-- Complete Button -->
    <div class="pt-4">
      <UButton
        block
        size="lg"
        color="primary"
        class="bg-gradient-to-r from-cyan-500 to-blue-600 font-semibold hover:from-cyan-600 hover:to-blue-700"
        :disabled="!consentChecked"
        @click="handleComplete"
      >
        <UIcon name="i-lucide-rocket" class="mr-2 h-5 w-5" />
        Complete Setup & Get Started
      </UButton>
      <p v-if="!consentChecked" class="mt-2 text-center text-xs text-gray-500 dark:text-gray-400">
        Please check the consent box to continue
      </p>
    </div>
  </div>
</template>
