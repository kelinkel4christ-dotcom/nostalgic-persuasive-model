<script setup lang="ts">
interface HabitLog {
  id: string
  date: string
  completed: boolean
  notes?: string | null
}

const props = defineProps<{
  habitType: 'exercise' | 'smoking_cessation'
  todayLog?: HabitLog | null
}>()

const emit = defineEmits<{
  logToday: []
}>()

// Format today's date
const today = new Date()
const formattedDate = today.toLocaleDateString('en-US', {
  weekday: 'long',
  month: 'long',
  day: 'numeric',
})

const habitLabel = computed(() => {
  return props.habitType === 'exercise' ? 'Exercise' : 'Smoke-Free'
})

const habitIcon = computed(() => {
  return props.habitType === 'exercise' ? 'i-lucide-dumbbell' : 'i-lucide-cigarette-off'
})

const statusInfo = computed(() => {
  if (!props.todayLog) {
    return {
      status: 'pending',
      label: 'Not logged yet',
      color: 'neutral',
      icon: 'i-lucide-circle-dashed',
    }
  }

  if (props.todayLog.completed) {
    return {
      status: 'completed',
      label: props.habitType === 'exercise' ? 'Workout done!' : 'Staying strong!',
      color: 'success',
      icon: 'i-lucide-check-circle-2',
    }
  }

  return {
    status: 'missed',
    label: props.habitType === 'exercise' ? 'Rest day' : 'Challenging day',
    color: 'error',
    icon: 'i-lucide-x-circle',
  }
})
</script>

<template>
  <UCard data-tutorial="today-status">
    <!-- Mobile: Stack vertically, Desktop: Row -->
    <div class="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
      <!-- Left: Icon + Text -->
      <div class="flex items-center gap-3">
        <div
          class="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl"
          :class="{
            'bg-green-100 dark:bg-green-900/30': statusInfo.status === 'completed',
            'bg-red-100 dark:bg-red-900/30': statusInfo.status === 'missed',
            'bg-neutral-100 dark:bg-neutral-800': statusInfo.status === 'pending',
          }"
        >
          <UIcon
            :name="habitIcon"
            class="text-2xl"
            :class="{
              'text-green-600 dark:text-green-400': statusInfo.status === 'completed',
              'text-red-600 dark:text-red-400': statusInfo.status === 'missed',
              'text-neutral-500': statusInfo.status === 'pending',
            }"
          />
        </div>
        <div class="min-w-0">
          <p class="text-sm text-muted">{{ formattedDate }}</p>
          <h3 class="text-lg font-semibold">{{ habitLabel }} Journey</h3>
        </div>
      </div>

      <!-- Right: Status + Button -->
      <div class="flex items-center justify-between gap-3 sm:justify-end">
        <div class="flex items-center gap-1.5">
          <UIcon
            :name="statusInfo.icon"
            :class="{
              'text-green-500': statusInfo.status === 'completed',
              'text-red-500': statusInfo.status === 'missed',
              'text-neutral-400': statusInfo.status === 'pending',
            }"
          />
          <span
            class="text-sm font-medium"
            :class="{
              'text-green-600 dark:text-green-400': statusInfo.status === 'completed',
              'text-red-600 dark:text-red-400': statusInfo.status === 'missed',
              'text-neutral-500': statusInfo.status === 'pending',
            }"
          >
            {{ statusInfo.label }}
          </span>
        </div>

        <UButton
          :color="statusInfo.status === 'pending' ? 'primary' : 'neutral'"
          :variant="statusInfo.status === 'pending' ? 'solid' : 'outline'"
          size="sm"
          @click="emit('logToday')"
        >
          {{ statusInfo.status === 'pending' ? 'Log Today' : 'Edit' }}
        </UButton>
      </div>
    </div>
  </UCard>
</template>
