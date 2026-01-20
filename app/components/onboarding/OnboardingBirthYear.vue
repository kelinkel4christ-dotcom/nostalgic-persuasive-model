<script setup lang="ts">
const emit = defineEmits<{
  next: [year: number]
}>()

const currentYear = new Date().getFullYear()
const minYear = 1940
const maxYear = currentYear - 10 // At least 10 years old

const birthYear = ref(1990)

// Generate year options for dropdown
const yearOptions = computed(() => {
  const years = []
  for (let year = maxYear; year >= minYear; year--) {
    years.push({ label: year.toString(), value: year })
  }
  return years
})

const currentAge = computed(() => currentYear - birthYear.value)

function handleNext() {
  emit('next', birthYear.value)
}
</script>

<template>
  <div class="space-y-8">
    <!-- Header -->
    <div class="text-center">
      <div
        class="mx-auto mb-6 flex h-20 w-20 items-center justify-center rounded-full bg-gradient-to-br from-violet-500/20 to-purple-600/20"
      >
        <UIcon name="i-lucide-calendar-heart" class="h-10 w-10 text-violet-500" />
      </div>
      <h2
        class="bg-gradient-to-r from-violet-500 to-purple-600 bg-clip-text text-2xl font-bold text-transparent"
      >
        When were you born?
      </h2>
      <p class="mt-2 text-gray-500 dark:text-gray-400">
        This helps us find content from your most nostalgic years
      </p>
    </div>

    <!-- Year Selection -->
    <div class="mx-auto max-w-xs space-y-6">
      <div class="relative">
        <USelectMenu
          v-model="birthYear"
          :items="yearOptions"
          value-key="value"
          class="w-full"
          size="xl"
          placeholder="Select your birth year"
        />
      </div>

      <!-- Age Display -->
      <div
        class="rounded-xl border border-violet-200 bg-gradient-to-r from-violet-50 to-purple-50 p-4 dark:border-violet-800/50 dark:from-violet-900/20 dark:to-purple-900/20"
      >
        <p class="text-center text-sm text-gray-600 dark:text-gray-300">
          That makes you
          <span class="font-bold text-violet-600 dark:text-violet-400"
            >{{ currentAge }} years old</span
          >
        </p>
      </div>

      <!-- Nostalgic Era Preview -->
      <div
        class="rounded-xl border border-gray-200 bg-gray-50 p-4 dark:border-gray-700 dark:bg-gray-800/50"
      >
        <p class="text-center text-xs text-gray-500 dark:text-gray-400">
          Your nostalgic era is likely
          <span class="font-semibold text-gray-700 dark:text-gray-200"
            >{{ birthYear + 5 }} - {{ birthYear + 19 }}</span
          >
        </p>
      </div>
    </div>

    <!-- Continue Button -->
    <div class="pt-4">
      <UButton
        block
        size="lg"
        color="primary"
        class="bg-gradient-to-r from-violet-500 to-purple-600 font-semibold hover:from-violet-600 hover:to-purple-700"
        @click="handleNext"
      >
        Continue
        <UIcon name="i-lucide-arrow-right" class="ml-2 h-4 w-4" />
      </UButton>
    </div>
  </div>
</template>
