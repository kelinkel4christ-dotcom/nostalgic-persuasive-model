<script setup lang="ts">
const props = defineProps<{
  open: boolean
  date: string
  habitType?: 'exercise' | 'smoking_cessation'
  initialCompleted?: boolean
  initialNotes?: string
  initialStressLevel?: number | null
  initialEmotion?: string | null
  loading?: boolean
}>()

const emit = defineEmits<{
  'update:open': [value: boolean]
  save: [
    data: {
      date: string
      completed: boolean
      notes: string
    },
  ]
}>()

// Form state
const completed = ref(props.initialCompleted ?? false)
const notes = ref(props.initialNotes ?? '')

// Reset form when date changes
watch(
  () => props.date,
  () => {
    completed.value = props.initialCompleted ?? false
    notes.value = props.initialNotes ?? ''
  }
)

watch(
  () => props.initialCompleted,
  (val) => {
    completed.value = val ?? true
  }
)

watch(
  () => props.initialNotes,
  (val) => {
    notes.value = val ?? ''
  }
)

function handleSave() {
  emit('save', {
    date: props.date,
    completed: completed.value,
    notes: notes.value,
  })
}

function handleClose() {
  emit('update:open', false)
}

// Format date for display
const formattedDate = computed(() => {
  if (!props.date) return ''
  const date = new Date(props.date + 'T00:00:00')
  return date.toLocaleDateString('en-US', {
    weekday: 'long',
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  })
})

// Check if this is a past date (read-only mode)
const isPastDate = computed(() => {
  if (!props.date) return false
  const today = new Date()
  today.setHours(0, 0, 0, 0)
  const selectedDate = new Date(props.date + 'T00:00:00')
  return selectedDate < today
})

// Word count (actual words, not characters)
const wordCount = computed(() => {
  const trimmed = notes.value.trim()
  if (!trimmed) return 0
  return trimmed.split(/\s+/).filter(Boolean).length
})

// Habit label
const habitLabel = computed(() => {
  return props.habitType === 'smoking_cessation'
    ? 'Did you stay smoke-free?'
    : 'Did you complete your exercise?'
})

// Status text for past entries
const statusText = computed(() => {
  if (completed.value) {
    return props.habitType === 'smoking_cessation' ? '🎉 Smoke-free!' : '💪 Completed!'
  }
  return props.habitType === 'smoking_cessation' ? '😔 Slipped up' : '❌ Missed'
})
</script>

<template>
  <UModal :open="open" @update:open="$emit('update:open', $event)">
    <template #content>
      <div class="flex w-full max-w-[500px] flex-col">
        <!-- Header -->
        <div
          class="flex items-start justify-between border-b border-gray-200 p-6 dark:border-white/10"
        >
          <div>
            <h2 class="text-xl font-bold text-gray-900 dark:text-white">
              {{ isPastDate ? 'View Entry' : 'Daily Journal' }}
            </h2>
            <p class="mt-1 text-sm text-gray-500 dark:text-gray-400">{{ formattedDate }}</p>
          </div>
          <UButton
            color="neutral"
            variant="ghost"
            icon="i-lucide-x"
            size="sm"
            @click="handleClose"
          />
        </div>

        <!-- Content -->
        <div class="flex max-h-[60vh] flex-col gap-6 overflow-y-auto p-6">
          <!-- Habit Status Section -->
          <div
            class="rounded-xl border border-gray-200 bg-gray-50 p-5 dark:border-white/10 dark:bg-white/5"
          >
            <div class="mb-4 flex items-center gap-3">
              <UIcon
                :name="
                  habitType === 'smoking_cessation' ? 'i-lucide-cigarette-off' : 'i-lucide-dumbbell'
                "
                class="text-xl text-primary"
              />
              <span class="font-medium text-gray-900 dark:text-white">{{ habitLabel }}</span>
            </div>

            <!-- Editable: Toggle buttons -->
            <div v-if="!isPastDate" class="flex gap-3">
              <UButton
                :color="completed ? 'success' : 'neutral'"
                :variant="completed ? 'solid' : 'outline'"
                size="lg"
                class="flex-1"
                @click="completed = true"
              >
                ✓ Yes
              </UButton>
              <UButton
                :color="!completed ? 'error' : 'neutral'"
                :variant="!completed ? 'solid' : 'outline'"
                size="lg"
                class="flex-1"
                @click="completed = false"
              >
                ✗ No
              </UButton>
            </div>

            <!-- Read-only: Status display -->
            <div
              v-else
              class="rounded-lg p-3 text-center text-xl font-semibold"
              :class="
                completed
                  ? 'bg-green-100 text-green-700 dark:bg-green-500/20 dark:text-green-500'
                  : 'bg-red-100 text-red-700 dark:bg-red-500/20 dark:text-red-500'
              "
            >
              {{ statusText }}
            </div>
          </div>

          <!-- Notes Section -->
          <div class="flex flex-col gap-3">
            <div class="flex items-center justify-between">
              <label class="font-medium text-gray-900 dark:text-white">
                <UIcon name="i-lucide-book-open" class="mr-1" />
                {{ isPastDate ? 'Notes' : 'How did it go?' }}
              </label>
              <span class="text-xs text-gray-500 dark:text-gray-400">{{ wordCount }} words</span>
            </div>

            <!-- Editable textarea -->
            <textarea
              v-if="!isPastDate"
              v-model="notes"
              class="min-h-[150px] w-full resize-y rounded-xl border border-gray-200 bg-white p-4 text-sm leading-relaxed text-gray-900 placeholder-gray-400 transition-colors focus:border-blue-500 focus:outline-none dark:border-white/10 dark:bg-black/30 dark:text-white dark:placeholder-white/40"
              placeholder="Write about your day... What went well? Any challenges? How did you feel?"
              rows="6"
            />

            <!-- Read-only display -->
            <div
              v-else
              class="min-h-[100px] rounded-xl bg-gray-50 p-4 leading-relaxed whitespace-pre-wrap text-gray-700 dark:bg-white/5 dark:text-white/80"
            >
              {{ notes || 'No notes for this day.' }}
            </div>
          </div>

          <!-- Analysis Section -->
          <div
            v-if="initialEmotion || initialStressLevel !== undefined"
            class="rounded-xl border border-gray-200 bg-gray-50 p-5 dark:border-white/10 dark:bg-white/5"
          >
            <h3 class="mb-3 font-medium text-gray-900 dark:text-white">Daily Analysis</h3>
            <div class="flex gap-4">
              <!-- Emotion -->
              <div v-if="initialEmotion" class="flex-1 rounded-lg bg-white p-3 dark:bg-black/20">
                <div class="mb-1 text-xs text-muted uppercase">Emotion</div>
                <div class="font-medium text-primary capitalize">{{ initialEmotion }}</div>
              </div>
              <!-- Stress -->
              <div
                v-if="initialStressLevel !== undefined && initialStressLevel !== null"
                class="flex-1 rounded-lg bg-white p-3 dark:bg-black/20"
              >
                <div class="mb-1 text-xs text-muted uppercase">Stress Level</div>
                <div class="flex items-center gap-2">
                  <div
                    class="h-2 w-2 rounded-full"
                    :class="
                      initialStressLevel < 0.3
                        ? 'bg-green-500'
                        : initialStressLevel < 0.6
                          ? 'bg-orange-500'
                          : 'bg-red-500'
                    "
                  />
                  <span class="font-medium">{{ initialStressLevel.toFixed(2) }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Footer - Only show save for today or future -->
        <div
          v-if="!isPastDate"
          class="flex gap-3 border-t border-gray-200 p-5 dark:border-white/10"
        >
          <UButton color="neutral" variant="outline" size="lg" @click="handleClose">
            Cancel
          </UButton>
          <UButton
            color="primary"
            size="lg"
            :loading="loading"
            icon="i-lucide-save"
            @click="handleSave"
          >
            Save Entry
          </UButton>
        </div>

        <!-- Footer for past dates - just close -->
        <div v-else class="flex border-t border-gray-200 p-5 dark:border-white/10">
          <UButton color="neutral" variant="soft" size="lg" class="w-full" @click="handleClose">
            Close
          </UButton>
        </div>
      </div>
    </template>
  </UModal>
</template>
