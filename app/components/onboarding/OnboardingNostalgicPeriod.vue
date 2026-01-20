<script setup lang="ts">
const props = defineProps<{
  birthYear: number
}>()

const emit = defineEmits<{
  next: [{ start: number; end: number }]
  skip: []
}>()

// Default nostalgic period: childhood (5-12) to teenage years (13-19)
const defaultStart = computed(() => props.birthYear + 5)
const defaultEnd = computed(() => Math.min(props.birthYear + 19, new Date().getFullYear() - 1))

const periodStart = ref(defaultStart.value)
const periodEnd = ref(defaultEnd.value)

// Era labels for context
const getEraLabel = (year: number) => {
  const decade = Math.floor(year / 10) * 10
  const labels: Record<number, string> = {
    1960: 'The Swinging Sixties',
    1970: 'The Groovy Seventies',
    1980: 'The Rad Eighties',
    1990: 'The Nostalgic Nineties',
    2000: 'The Y2K Era',
    2010: 'The Twenty-Tens',
    2020: 'The Twenty-Twenties',
  }
  return labels[decade] || `${decade}s`
}

const periodYears = computed(() => periodEnd.value - periodStart.value + 1)

const showValidation = computed(() => periodEnd.value < periodStart.value)

function handleNext() {
  emit('next', { start: periodStart.value, end: periodEnd.value })
}

function handleSkip() {
  emit('skip')
}

// Generate year options
const startYearOptions = computed(() => {
  const years = []
  const minYear = props.birthYear
  const maxYear = new Date().getFullYear() - 1
  for (let year = minYear; year <= maxYear; year++) {
    years.push({ label: year.toString(), value: year })
  }
  return years
})

const endYearOptions = computed(() => {
  const years = []
  const minYear = periodStart.value
  const maxYear = new Date().getFullYear() - 1
  for (let year = minYear; year <= maxYear; year++) {
    years.push({ label: year.toString(), value: year })
  }
  return years
})
</script>

<template>
  <div class="space-y-8">
    <!-- Header -->
    <div class="text-center">
      <div
        class="mx-auto mb-6 flex h-20 w-20 items-center justify-center rounded-full bg-gradient-to-br from-amber-500/20 to-orange-600/20"
      >
        <UIcon name="i-lucide-sparkles" class="h-10 w-10 text-amber-500" />
      </div>
      <h2
        class="bg-gradient-to-r from-amber-500 to-orange-600 bg-clip-text text-2xl font-bold text-transparent"
      >
        Your Nostalgic Years
      </h2>
      <p class="mt-2 text-gray-500 dark:text-gray-400">
        What time period brings back the warmest memories?
      </p>
    </div>

    <!-- Period Selection -->
    <div class="space-y-6">
      <div class="grid grid-cols-2 gap-4">
        <div class="space-y-2">
          <label class="text-sm font-medium text-gray-700 dark:text-gray-300">From</label>
          <USelectMenu
            v-model="periodStart"
            :items="startYearOptions"
            value-key="value"
            class="w-full"
            size="lg"
          />
        </div>
        <div class="space-y-2">
          <label class="text-sm font-medium text-gray-700 dark:text-gray-300">To</label>
          <USelectMenu
            v-model="periodEnd"
            :items="endYearOptions"
            value-key="value"
            class="w-full"
            size="lg"
          />
        </div>
      </div>

      <!-- Validation Error -->
      <p v-if="showValidation" class="text-center text-sm text-red-500">
        End year must be after start year
      </p>

      <!-- Era Summary -->
      <div
        class="rounded-xl border border-amber-200 bg-gradient-to-r from-amber-50 to-orange-50 p-4 dark:border-amber-800/50 dark:from-amber-900/20 dark:to-orange-900/20"
      >
        <div class="flex items-center justify-between">
          <div>
            <p class="text-sm font-medium text-gray-700 dark:text-gray-200">
              {{ getEraLabel(periodStart) }}
              {{
                periodStart !== periodEnd && periodEnd - periodStart > 5
                  ? `to ${getEraLabel(periodEnd)}`
                  : ''
              }}
            </p>
            <p class="text-xs text-gray-500 dark:text-gray-400">
              {{ periodYears }} year{{ periodYears > 1 ? 's' : '' }} of memories
            </p>
          </div>
          <div class="flex h-10 w-10 items-center justify-center rounded-full bg-amber-500/20">
            <UIcon name="i-lucide-music" class="h-5 w-5 text-amber-600 dark:text-amber-400" />
          </div>
        </div>
      </div>

      <!-- Default Suggestion -->
      <p class="text-center text-xs text-gray-500 dark:text-gray-400">
        We've pre-selected your childhood and teenage years (ages 5-19), which are typically the
        most nostalgic.
      </p>
    </div>

    <!-- Actions -->
    <div class="space-y-3 pt-4">
      <UButton
        block
        size="lg"
        color="primary"
        class="bg-gradient-to-r from-amber-500 to-orange-600 font-semibold hover:from-amber-600 hover:to-orange-700"
        :disabled="showValidation"
        @click="handleNext"
      >
        Continue with {{ periodStart }} - {{ periodEnd }}
        <UIcon name="i-lucide-arrow-right" class="ml-2 h-4 w-4" />
      </UButton>
      <UButton block size="lg" variant="ghost" color="neutral" @click="handleSkip">
        Skip & use defaults
      </UButton>
    </div>
  </div>
</template>
