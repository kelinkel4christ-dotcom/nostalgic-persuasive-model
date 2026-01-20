<script setup lang="ts">
import { today, getLocalTimeZone } from '@internationalized/date'

definePageMeta({
  auth: true,
})

const authStore = useAuthStore()
const tutorialStore = useTutorialStore()

interface HabitLog {
  id: string
  date: string
  completed: boolean
  notes?: string | null
  stressLevel?: number | null
  emotion?: string | null
}

interface Preferences {
  birthYear: number | null
  nostalgicPeriodStart: number | null
  nostalgicPeriodEnd: number | null
  habitType: 'exercise' | 'smoking_cessation'
  experimentGroup: 'treatment' | 'control'
  onboardingCompletedAt: string | null
}

// Fetch user preferences
const { data: prefsData, status: prefsStatus } = await useFetch<{
  preferences: Preferences | null
  onboardingComplete: boolean
}>('/api/habits/preferences', { lazy: true })

// Fetch tutorial status (SSR-friendly to prevent flickering)
const { data: tutorialData } = await useFetch<{ completed: boolean; skipped: boolean }>(
  '/api/tutorial/status'
)

if (tutorialData.value) {
  tutorialStore.hasCompletedTutorial = tutorialData.value.completed
  tutorialStore.hasSkippedTutorial = tutorialData.value.skipped
}

// Set experiment group for group-specific tutorial
if (prefsData.value?.preferences?.experimentGroup) {
  tutorialStore.experimentGroup = prefsData.value.preferences.experimentGroup
}

// Auto-start tutorial logic
onMounted(() => {
  // Auto-start tutorial 2 seconds after onboarding completion
  if (!tutorialStore.hasCompletedTutorial && !tutorialStore.hasSkippedTutorial) {
    setTimeout(() => {
      tutorialStore.startTour()
    }, 2000)
  }
})

// Current month for logs
const currentMonth = ref(formatMonth(today(getLocalTimeZone())))

function formatMonth(date: { year: number; month: number }): string {
  return `${date.year}-${String(date.month).padStart(2, '0')}`
}

// Fetch habit logs for current month
const {
  data: logsData,
  refresh: refreshLogs,
  status: logsStatus,
} = await useFetch<{ logs: HabitLog[]; period: { startDate: string; endDate: string } }>(
  '/api/habits/logs',
  {
    query: { month: currentMonth },
    lazy: true,
    watch: [currentMonth],
  }
)

// Modal state
const logModalOpen = ref(false)
const selectedDate = ref('')
const savingLog = ref(false)

// Get today's log
const todayStr = computed(() => {
  const now = new Date()
  return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-${String(now.getDate()).padStart(2, '0')}`
})

const todayLog = computed(() => {
  return logsData.value?.logs.find((log) => log.date === todayStr.value) ?? null
})

// Get selected day log
const selectedDayLog = computed(() => {
  return logsData.value?.logs.find((log) => log.date === selectedDate.value) ?? null
})

// Handle day click from calendar
function handleDayClick(date: string) {
  selectedDate.value = date
  logModalOpen.value = true
}

// Handle month change
function handleMonthChange(year: number, month: number) {
  currentMonth.value = `${year}-${String(month).padStart(2, '0')}`
}

// Handle log today button
function handleLogToday() {
  selectedDate.value = todayStr.value
  logModalOpen.value = true
}

// Save log entry
async function handleSaveLog(data: { date: string; completed: boolean; notes: string }) {
  savingLog.value = true
  try {
    await $fetch('/api/habits/logs', {
      method: 'POST',
      body: data,
    })
    await refreshLogs()
    logModalOpen.value = false
  } catch (error) {
    console.error('Failed to save log:', error)
  } finally {
    savingLog.value = false
  }
}

// Check if user needs to complete onboarding
const needsOnboarding = computed(() => {
  return prefsStatus.value === 'success' && !prefsData.value?.onboardingComplete
})

// Habit type for display
const habitType = computed(() => prefsData.value?.preferences?.habitType ?? 'exercise')
</script>

<template>
  <UContainer class="space-y-6 py-8">
    <!-- Redirect to onboarding if needed -->
    <div v-if="needsOnboarding" class="py-12 text-center">
      <h2 class="mb-4 text-2xl font-semibold">Welcome! Let's get you started.</h2>
      <p class="mb-6 text-muted">Complete the onboarding to set up your personalized journey.</p>
      <UButton color="primary" size="lg" to="/onboarding"> Start Onboarding </UButton>
    </div>

    <!-- Main Dashboard -->
    <template v-else>
      <!-- Header -->
      <div>
        <h1 class="text-3xl font-bold tracking-tight">
          Welcome back, {{ authStore.user?.name?.split(' ')[0] || 'there' }}! 👋
        </h1>
        <p class="mt-2 text-muted">
          Your
          <span class="font-medium">{{ habitType === 'exercise' ? 'fitness' : 'smoke-free' }}</span>
          journey continues.
        </p>
      </div>

      <!-- Top Row: Today Status + Recommendation -->
      <div class="grid gap-6 lg:grid-cols-2">
        <!-- Today's Status -->
        <HomeTodayStatus
          :habit-type="habitType"
          :today-log="todayLog"
          @log-today="handleLogToday"
        />

        <!-- Recommendation Card (Both Treatment & Control) -->
        <HomeNostalgicRecommendationCard
          :loading="prefsStatus === 'pending'"
          :experiment-group="prefsData?.preferences?.experimentGroup"
        />
      </div>

      <!-- Second Row: Stress & Emotion Chart -->
      <HomeStressEmotionChart :logs="logsData?.logs ?? []" />

      <!-- Calendar -->
      <HomeHabitCalendar
        :logs="logsData?.logs ?? []"
        :loading="logsStatus === 'pending'"
        @day-click="handleDayClick"
        @month-change="handleMonthChange"
      />

      <!-- Log Modal -->
      <HomeDailyLogModal
        v-model:open="logModalOpen"
        :date="selectedDate"
        :habit-type="habitType"
        :initial-completed="selectedDayLog?.completed"
        :initial-notes="selectedDayLog?.notes ?? ''"
        :initial-stress-level="selectedDayLog?.stressLevel"
        :initial-emotion="selectedDayLog?.emotion"
        :loading="savingLog"
        @save="handleSaveLog"
      />

      <!-- Tutorial Overlay -->
      <TutorialOverlay v-if="tutorialStore.isActive" />

      <!-- Take Tour Button -->
      <TutorialTakeTourButton v-else-if="tutorialStore.showTakeTourButton" />
    </template>
  </UContainer>
</template>
