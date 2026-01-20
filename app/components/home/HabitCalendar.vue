<script setup lang="ts">
import { CalendarDate, today, getLocalTimeZone } from '@internationalized/date'

interface HabitLog {
  id: string
  date: string
  completed: boolean
  notes?: string | null
  stressLevel?: number | null
  emotion?: string | null
}

const props = defineProps<{
  logs: HabitLog[]
  loading?: boolean
}>()

const emit = defineEmits<{
  dayClick: [date: string]
  monthChange: [year: number, month: number]
}>()

// Current displayed month
const displayedDate = ref(today(getLocalTimeZone()))

// Watch for month changes
watch(displayedDate, (newDate) => {
  emit('monthChange', newDate.year, newDate.month)
})

// Create a map of date -> log for quick lookup
const logMap = computed(() => {
  const map = new Map<string, HabitLog>()
  props.logs.forEach((log) => {
    map.set(log.date, log)
  })
  return map
})

// Stats for the current month
const monthStats = computed(() => {
  const completed = props.logs.filter((log) => log.completed).length
  const missed = props.logs.filter((log) => !log.completed).length
  return { completed, missed, total: completed + missed }
})

function handleDayClick(date: CalendarDate) {
  const dateStr = `${date.year}-${String(date.month).padStart(2, '0')}-${String(date.day).padStart(2, '0')}`
  emit('dayClick', dateStr)
}

function getDayStatus(date: CalendarDate): 'completed' | 'missed' | 'future' | 'none' {
  const todayDate = today(getLocalTimeZone())
  const dateStr = `${date.year}-${String(date.month).padStart(2, '0')}-${String(date.day).padStart(2, '0')}`

  // Future dates
  if (date.compare(todayDate) > 0) {
    return 'future'
  }

  const log = logMap.value.get(dateStr)
  if (!log) return 'none'
  return log.completed ? 'completed' : 'missed'
}

// Generate calendar grid
const currentMonthDays = computed(() => {
  const year = displayedDate.value.year
  const month = displayedDate.value.month
  const lastDay = new Date(year, month, 0).getDate()

  const days: CalendarDate[] = []
  for (let d = 1; d <= lastDay; d++) {
    days.push(new CalendarDate(year, month, d))
  }
  return days
})

// Get the weekday offset for the first day of month (0 = Sunday)
const firstDayOffset = computed(() => {
  const year = displayedDate.value.year
  const month = displayedDate.value.month
  return new Date(year, month - 1, 1).getDay()
})

// Month name for display
const monthName = computed(() => {
  const date = new Date(displayedDate.value.year, displayedDate.value.month - 1)
  return date.toLocaleDateString('en-US', { month: 'long', year: 'numeric' })
})

function prevMonth() {
  const current = displayedDate.value
  if (current.month === 1) {
    displayedDate.value = new CalendarDate(current.year - 1, 12, 1)
  } else {
    displayedDate.value = new CalendarDate(current.year, current.month - 1, 1)
  }
}

function nextMonth() {
  const current = displayedDate.value
  if (current.month === 12) {
    displayedDate.value = new CalendarDate(current.year + 1, 1, 1)
  } else {
    displayedDate.value = new CalendarDate(current.year, current.month + 1, 1)
  }
}

// Helpers for Emotion and Stress
function getStressColor(level: number | null | undefined): string {
  if (level === null || level === undefined) return 'bg-gray-200 dark:bg-gray-700'
  if (level < 0.3) return 'bg-green-400'
  if (level < 0.6) return 'bg-orange-400'
  return 'bg-red-400'
}

function getLogForDate(date: CalendarDate) {
  const dateStr = `${date.year}-${String(date.month).padStart(2, '0')}-${String(date.day).padStart(2, '0')}`
  return logMap.value.get(dateStr)
}
</script>

<template>
  <UCard data-tutorial="habit-calendar" class="habit-calendar">
    <template #header>
      <!-- Mobile: Stack, Desktop: Row -->
      <div class="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
        <h3 class="text-lg font-semibold">Your Journey</h3>
        <div class="flex items-center gap-3 text-sm sm:gap-4">
          <span class="flex items-center gap-1.5">
            <span class="h-2.5 w-2.5 rounded-full bg-green-500 sm:h-3 sm:w-3" />
            <span class="text-xs sm:text-sm">{{ monthStats.completed }} completed</span>
          </span>
          <span class="flex items-center gap-1.5">
            <span class="h-2.5 w-2.5 rounded-full bg-red-500 sm:h-3 sm:w-3" />
            <span class="text-xs sm:text-sm">{{ monthStats.missed }} missed</span>
          </span>
        </div>
      </div>
    </template>

    <!-- Calendar Container with overflow handling -->
    <div class="calendar-container">
      <!-- Month Navigation -->
      <div class="mb-4 flex items-center justify-between sm:mb-6">
        <UButton
          color="neutral"
          variant="ghost"
          icon="i-lucide-chevron-left"
          size="sm"
          @click="prevMonth"
        />
        <h4 class="text-base font-semibold sm:text-lg">{{ monthName }}</h4>
        <UButton
          color="neutral"
          variant="ghost"
          icon="i-lucide-chevron-right"
          size="sm"
          @click="nextMonth"
        />
      </div>

      <!-- Weekday Headers -->
      <div class="calendar-grid mb-1 sm:mb-2">
        <div v-for="day in ['S', 'M', 'T', 'W', 'T', 'F', 'S']" :key="day" class="calendar-header">
          {{ day }}
        </div>
      </div>

      <!-- Calendar Days -->
      <div class="calendar-grid">
        <!-- Empty cells for offset -->
        <div v-for="n in firstDayOffset" :key="'offset-' + n" class="calendar-cell empty" />

        <!-- Actual days -->
        <button
          v-for="day in currentMonthDays"
          :key="day.toString()"
          class="calendar-cell"
          :class="{
            'cell-completed': getDayStatus(day) === 'completed',
            'cell-missed': getDayStatus(day) === 'missed',
            'cell-future': getDayStatus(day) === 'future',
            'cell-none': getDayStatus(day) === 'none',
            'cell-today': day.compare(today(getLocalTimeZone())) === 0,
          }"
          :disabled="loading || getDayStatus(day) === 'future'"
          @click="handleDayClick(day)"
        >
          <div class="flex h-full w-full flex-col justify-between p-0.5 sm:p-1">
            <div class="flex w-full items-start justify-between">
              <span class="day-number">{{ day.day }}</span>
              <!-- Completion Icon -->
              <span v-if="getDayStatus(day) === 'completed'" class="status-icon">✓</span>
              <span v-else-if="getDayStatus(day) === 'missed'" class="status-icon">✗</span>
            </div>

            <!-- Emotion & Stress (Only for completed/missed with data) -->
            <div
              v-if="
                (getDayStatus(day) === 'completed' || getDayStatus(day) === 'missed') &&
                getLogForDate(day)?.emotion
              "
              class="flex w-full flex-col items-center gap-0.5"
            >
              <span
                class="w-full truncate text-center text-[9px] leading-tight font-medium sm:text-[10px]"
              >
                {{ getLogForDate(day)?.emotion }}
              </span>
              <div class="flex items-center gap-1">
                <span
                  :class="getStressColor(getLogForDate(day)?.stressLevel)"
                  class="h-1.5 w-1.5 rounded-full"
                />
                <span class="text-[8px] font-medium opacity-80 sm:text-[9px]">
                  {{ getLogForDate(day)?.stressLevel?.toFixed(1) }}
                </span>
              </div>
            </div>
          </div>
        </button>
      </div>
    </div>
  </UCard>
</template>

<style scoped>
.calendar-container {
  width: 100%;
  overflow-x: auto;
  padding: 0.25rem;
}

@media (min-width: 640px) {
  .calendar-container {
    padding: 0.5rem;
  }
}

.calendar-grid {
  display: grid;
  grid-template-columns: repeat(7, minmax(40px, 1fr));
  gap: 4px;
}

@media (min-width: 640px) {
  .calendar-grid {
    gap: 8px;
    grid-template-columns: repeat(7, 1fr);
  }
}

.calendar-header {
  text-align: center;
  font-size: 0.6875rem;
  font-weight: 600;
  color: rgb(156, 163, 175);
  text-transform: uppercase;
  padding: 0.25rem;
}

@media (min-width: 640px) {
  .calendar-header {
    font-size: 0.75rem;
    padding: 0.5rem;
  }
}

.calendar-cell {
  aspect-ratio: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  border-radius: 0.5rem;
  cursor: pointer;
  transition: all 0.2s ease;
  position: relative;
  min-height: 44px;
  min-width: 40px;
  border: 2px solid transparent;
  overflow: hidden;
}

@media (min-width: 640px) {
  .calendar-cell {
    min-height: 60px;
    border-radius: 0.75rem;
  }
}

.calendar-cell:not(.empty):hover:not(:disabled) {
  transform: scale(1.05);
}

.calendar-cell.empty {
  cursor: default;
}

.day-number {
  font-size: 0.75rem;
  font-weight: 500;
  line-height: 1;
}

@media (min-width: 640px) {
  .day-number {
    font-size: 0.875rem;
  }
}

.status-icon {
  font-size: 0.625rem;
  line-height: 1;
}

@media (min-width: 640px) {
  .status-icon {
    font-size: 0.75rem;
  }
}

/* Completed (Green) */
.cell-completed {
  background: linear-gradient(135deg, rgba(34, 197, 94, 0.2), rgba(34, 197, 94, 0.3));
  border-color: rgb(34, 197, 94);
  color: rgb(34, 197, 94);
}

.cell-completed .status-icon {
  color: rgb(34, 197, 94);
}

.cell-completed:hover {
  background: linear-gradient(135deg, rgba(34, 197, 94, 0.3), rgba(34, 197, 94, 0.4));
}

/* Missed (Red) */
.cell-missed {
  background: linear-gradient(135deg, rgba(239, 68, 68, 0.2), rgba(239, 68, 68, 0.3));
  border-color: rgb(239, 68, 68);
  color: rgb(239, 68, 68);
}

.cell-missed .status-icon {
  color: rgb(239, 68, 68);
}

.cell-missed:hover {
  background: linear-gradient(135deg, rgba(239, 68, 68, 0.3), rgba(239, 68, 68, 0.4));
}

/* Future (Disabled) */
.cell-future {
  color: rgb(75, 85, 99);
  opacity: 0.4;
  cursor: not-allowed;
}

.cell-future:hover {
  transform: none;
}

/* No entry yet */
.cell-none {
  background: rgba(107, 114, 128, 0.1);
  color: rgb(156, 163, 175);
}

.cell-none:hover {
  background: rgba(107, 114, 128, 0.2);
  border-color: rgba(107, 114, 128, 0.3);
}

/* Today highlight - uses thicker blue border, not shadow */
.cell-today {
  border-width: 3px;
  border-color: rgb(59, 130, 246) !important;
}

/* When today AND completed, show blue border with green background */
.cell-today.cell-completed {
  background: linear-gradient(135deg, rgba(34, 197, 94, 0.25), rgba(34, 197, 94, 0.35));
}

/* When today AND missed, show blue border with red background */
.cell-today.cell-missed {
  background: linear-gradient(135deg, rgba(239, 68, 68, 0.25), rgba(239, 68, 68, 0.35));
}
</style>
