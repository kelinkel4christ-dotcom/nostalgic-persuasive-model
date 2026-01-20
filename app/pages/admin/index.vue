<script setup lang="ts">
definePageMeta({
  layout: 'default',
  auth: false, // Uses custom admin auth
})

const router = useRouter()

// Types
interface StatsData {
  overview: {
    totalUsers: number
    activeUsers: number
    treatmentUsers: number
    controlUsers: number
    totalHabitLogs: number
  }
  engagement: {
    avgTimeOnPlatform: number
    regretRate: number
    avgInteractions: number
  }
  groupBehavior: {
    treatment: GroupMetrics
    control: GroupMetrics
  }
  stressComparison: {
    treatment: { avgStress: number | null; logCount: number }
    control: { avgStress: number | null; logCount: number }
  }
  completionComparison: {
    treatment: { total: number; completed: number; rate: number }
    control: { total: number; completed: number; rate: number }
  }
  nostalgiaFeedback: {
    total: number
    positive: number
    positiveRate: number
  }
}

interface GroupMetrics {
  views: number
  clicks: number
  skips: number
  replays: number
  feedback: number
  totalInteractions: number
  totalDuration: number
  regretRate: number
  ctr: number
  positiveResponseRate: number
  viewsPerUser: number
  interactionsPerUser: number
  durationPerUser: number
  durationPerView: number
}

interface GroupComparison {
  emotions: {
    treatment: Record<string, number>
    control: Record<string, number>
  }
  stressDistribution: {
    treatment: { low: number; medium: number; high: number }
    control: { low: number; medium: number; high: number }
  }
}

// Fetch data
const {
  data: stats,
  error: statsError,
  refresh: refreshStats,
} = await useFetch<StatsData>('/api/admin/stats', {
  lazy: true,
  onResponseError: ({ response }) => {
    if (response.status === 401) {
      router.push('/admin/login')
    }
  },
})

const { data: comparison, refresh: refreshComparison } = await useFetch<GroupComparison>(
  '/api/admin/group-comparison',
  { lazy: true }
)

// Check auth on mount
onMounted(() => {
  if (statsError.value?.statusCode === 401) {
    router.push('/admin/login')
  }
})

// Logout
async function handleLogout() {
  await $fetch('/api/admin/logout', { method: 'POST' })
  router.push('/admin/login')
}

// Export CSV
function exportCsv() {
  window.open('/api/admin/export-csv', '_blank')
}

// Export Interactions CSV
function exportInteractions() {
  window.open('/api/admin/export-interactions', '_blank')
}

// Refresh all data
async function refreshData() {
  await Promise.all([refreshStats(), refreshComparison()])
}

// Formatters
function formatPct(value: number | null | undefined): string {
  if (value === null || value === undefined) return 'N/A'
  return `${value.toFixed(1)}%`
}

function formatStress(value: number | null | undefined): string {
  if (value === null || value === undefined) return 'N/A'
  return value.toFixed(3)
}

function formatDuration(seconds: number): string {
  if (!seconds) return '0s'
  const m = Math.floor(seconds / 60)
  const s = Math.round(seconds % 60)
  return m > 0 ? `${m}m ${s}s` : `${s}s`
}

// Get all unique emotions
const allEmotions = computed(() => {
  if (!comparison.value) return []
  const emotions = new Set([
    ...Object.keys(comparison.value.emotions.treatment),
    ...Object.keys(comparison.value.emotions.control),
  ])
  return Array.from(emotions).sort()
})

// Comparison Helpers
const betterGroup = (metric: keyof GroupMetrics, higherIsBetter: boolean = true) => {
  if (!stats.value) return null
  const t = stats.value.groupBehavior.treatment[metric]
  const c = stats.value.groupBehavior.control[metric]
  if (t === c) return null
  if (higherIsBetter) return t > c ? 'treatment' : 'control'
  return t < c ? 'treatment' : 'control'
}
</script>

<template>
  <UContainer class="space-y-6 py-4 sm:space-y-8 sm:py-8">
    <!-- Header -->
    <div class="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
      <div>
        <h1 class="text-2xl font-bold sm:text-3xl">Admin Dashboard</h1>
        <p class="mt-1 text-sm text-muted sm:text-base">Research analytics & group comparison</p>
      </div>
      <div class="grid grid-cols-2 gap-2 sm:flex sm:items-center sm:gap-3">
        <UButton
          color="neutral"
          variant="soft"
          icon="i-lucide-refresh-cw"
          class="justify-center sm:flex-none"
          @click="refreshData"
        >
          Refresh
        </UButton>
        <UButton
          color="primary"
          variant="soft"
          icon="i-lucide-file-text"
          class="justify-center sm:flex-none"
          @click="exportCsv"
        >
          Habit Logs
        </UButton>
        <UButton
          color="primary"
          icon="i-lucide-activity"
          class="justify-center sm:flex-none"
          @click="exportInteractions"
        >
          Interactions
        </UButton>
        <UButton
          color="neutral"
          variant="ghost"
          icon="i-lucide-log-out"
          class="justify-center sm:flex-none"
          @click="handleLogout"
        >
          Logout
        </UButton>
      </div>
    </div>

    <!-- Overview Stats -->
    <div class="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
      <UCard>
        <div class="text-center">
          <p class="text-sm text-muted">Total Users</p>
          <p class="text-3xl font-bold">{{ stats?.overview.totalUsers ?? '—' }}</p>
        </div>
      </UCard>
      <UCard>
        <div class="text-center">
          <p class="text-sm text-muted">Nostalgia Group</p>
          <p class="text-3xl font-bold text-amber-500">
            {{ stats?.overview.treatmentUsers ?? '—' }}
          </p>
        </div>
      </UCard>
      <UCard>
        <div class="text-center">
          <p class="text-sm text-muted">Control Group</p>
          <p class="text-3xl font-bold text-slate-500">
            {{ stats?.overview.controlUsers ?? '—' }}
          </p>
        </div>
      </UCard>
      <UCard>
        <div class="text-center">
          <p class="text-sm text-muted">Total Habit Logs</p>
          <p class="text-3xl font-bold">{{ stats?.overview.totalHabitLogs ?? '—' }}</p>
        </div>
      </UCard>
    </div>

    <!-- NEW: Engagement & Quality Metrics -->
    <div class="space-y-2">
      <h2 class="flex items-center gap-2 text-xl font-bold">
        <UIcon name="i-lucide-activity" class="text-primary" />
        Engagement & Quality
      </h2>
      <div class="grid gap-4 sm:grid-cols-3">
        <UCard class="relative overflow-hidden">
          <div class="relative z-10">
            <p class="text-sm font-medium text-muted">Avg Content Dwell Time</p>
            <p class="mt-1 text-3xl font-bold text-primary">
              {{ formatDuration(stats?.engagement.avgTimeOnPlatform ?? 0) }}
            </p>
            <p
              class="mt-2 inline-block rounded bg-gray-100 p-1 font-mono text-xs text-muted dark:bg-gray-800"
            >
              ∑ View Duration / Active Users
            </p>
          </div>
          <UIcon
            name="i-lucide-clock"
            class="absolute -right-4 -bottom-4 text-9xl text-primary/5"
          />
        </UCard>

        <UCard class="relative overflow-hidden">
          <div class="relative z-10">
            <p class="text-sm font-medium text-muted">Regret Score</p>
            <p class="mt-1 text-3xl font-bold text-red-500">
              {{ formatPct(stats?.engagement.regretRate) }}
            </p>
            <p
              class="mt-2 inline-block rounded bg-gray-100 p-1 font-mono text-xs text-muted dark:bg-gray-800"
            >
              Skips / Total Views
            </p>
          </div>
          <UIcon
            name="i-lucide-frown"
            class="absolute -right-4 -bottom-4 text-9xl text-red-500/5"
          />
        </UCard>

        <UCard class="relative">
          <div class="relative z-10">
            <div class="flex items-center gap-2">
              <p class="text-sm font-medium text-muted">Interaction Volume</p>
              <UPopover mode="hover" side="top">
                <UIcon
                  name="i-lucide-info"
                  class="h-4 w-4 cursor-help text-gray-400 hover:text-gray-600"
                />
                <template #content>
                  <div class="space-y-1 p-3 text-xs">
                    <p class="mb-2 font-semibold">Counted Events:</p>
                    <ul class="list-inside list-disc space-y-1 text-gray-600 dark:text-gray-300">
                      <li>Views (Card shown)</li>
                      <li>Clicks (Spotify/Trailer)</li>
                      <li>Skips (Immediate rejection)</li>
                      <li>Nexts (Engaged refresh)</li>
                      <li>Feedback (Ratings)</li>
                    </ul>
                  </div>
                </template>
              </UPopover>
            </div>
            <p class="mt-1 text-3xl font-bold text-blue-500">
              {{ stats?.engagement.avgInteractions.toFixed(1) ?? '—' }}
            </p>
            <p
              class="mt-2 inline-block rounded bg-gray-100 p-1 font-mono text-xs text-muted dark:bg-gray-800"
            >
              Total Events / Active Users
            </p>
          </div>
          <div class="pointer-events-none absolute inset-0 overflow-hidden">
            <UIcon
              name="i-lucide-mouse-pointer-click"
              class="absolute -right-4 -bottom-4 text-9xl text-blue-500/5"
            />
          </div>
        </UCard>
      </div>
    </div>

    <!-- NEW: Group Behavior Analysis Table -->
    <UCard>
      <template #header>
        <div class="flex items-center gap-2">
          <UIcon name="i-lucide-users" class="text-xl text-primary" />
          <h2 class="text-lg font-semibold">Group Behavior Analysis</h2>
        </div>
      </template>

      <div class="overflow-x-auto">
        <table class="w-full text-sm">
          <thead>
            <tr class="border-b bg-gray-50 dark:bg-gray-800/50">
              <th class="px-4 py-3 text-left font-semibold text-muted">Metric</th>
              <th class="px-4 py-3 text-right font-semibold text-amber-600">
                <span class="hidden sm:inline">Nostalgia (Group A)</span>
                <span class="sm:hidden">Nostalgia</span>
              </th>
              <th class="px-4 py-3 text-right font-semibold text-slate-600">
                <span class="hidden sm:inline">Control (Group B)</span>
                <span class="sm:hidden">Control</span>
              </th>
              <th class="px-4 py-3 text-center font-semibold text-primary">Winner</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-gray-100 dark:divide-gray-800">
            <tr>
              <td class="px-4 py-3">Views / User</td>
              <td class="px-4 py-3 text-right font-mono">
                {{ stats?.groupBehavior.treatment.viewsPerUser.toFixed(1) }}
              </td>
              <td class="px-4 py-3 text-right font-mono">
                {{ stats?.groupBehavior.control.viewsPerUser.toFixed(1) }}
              </td>
              <td class="px-4 py-3 text-center">
                <UBadge
                  v-if="betterGroup('viewsPerUser') === 'treatment'"
                  color="secondary"
                  variant="subtle"
                  size="xs"
                  >Nostalgia</UBadge
                >
                <UBadge
                  v-else-if="betterGroup('viewsPerUser') === 'control'"
                  color="neutral"
                  variant="subtle"
                  size="xs"
                  >Control</UBadge
                >
                <span v-else class="text-xs text-muted">—</span>
              </td>
            </tr>
            <tr>
              <td class="px-4 py-3">Click-Through Rate (CTR)</td>
              <td class="px-4 py-3 text-right font-mono">
                {{ formatPct(stats?.groupBehavior.treatment.ctr) }}
              </td>
              <td class="px-4 py-3 text-right font-mono">
                {{ formatPct(stats?.groupBehavior.control.ctr) }}
              </td>
              <td class="px-4 py-3 text-center">
                <UBadge
                  v-if="betterGroup('ctr') === 'treatment'"
                  color="secondary"
                  variant="subtle"
                  size="xs"
                  >Nostalgia</UBadge
                >
                <UBadge
                  v-else-if="betterGroup('ctr') === 'control'"
                  color="neutral"
                  variant="subtle"
                  size="xs"
                  >Control</UBadge
                >
                <span v-else class="text-xs text-muted">—</span>
              </td>
            </tr>
            <tr>
              <td class="px-4 py-3">Regret Rate (Lower is Better)</td>
              <td class="px-4 py-3 text-right font-mono">
                {{ formatPct(stats?.groupBehavior.treatment.regretRate) }}
              </td>
              <td class="px-4 py-3 text-right font-mono">
                {{ formatPct(stats?.groupBehavior.control.regretRate) }}
              </td>
              <td class="px-4 py-3 text-center">
                <UBadge
                  v-if="betterGroup('regretRate', false) === 'treatment'"
                  color="secondary"
                  variant="subtle"
                  size="xs"
                  >Nostalgia</UBadge
                >
                <UBadge
                  v-else-if="betterGroup('regretRate', false) === 'control'"
                  color="neutral"
                  variant="subtle"
                  size="xs"
                  >Control</UBadge
                >
                <span v-else class="text-xs text-muted">—</span>
              </td>
            </tr>
            <tr>
              <td class="px-4 py-3">Avg Duration / User</td>
              <td class="px-4 py-3 text-right font-mono">
                {{ formatDuration(stats?.groupBehavior.treatment.durationPerUser ?? 0) }}
              </td>
              <td class="px-4 py-3 text-right font-mono">
                {{ formatDuration(stats?.groupBehavior.control.durationPerUser ?? 0) }}
              </td>
              <td class="px-4 py-3 text-center">
                <UBadge
                  v-if="betterGroup('durationPerUser') === 'treatment'"
                  color="secondary"
                  variant="subtle"
                  size="xs"
                  >Nostalgia</UBadge
                >
                <UBadge
                  v-else-if="betterGroup('durationPerUser') === 'control'"
                  color="neutral"
                  variant="subtle"
                  size="xs"
                  >Control</UBadge
                >
                <span v-else class="text-xs text-muted">—</span>
              </td>
            </tr>
            <tr>
              <td class="px-4 py-3">Avg Duration / View</td>
              <td class="px-4 py-3 text-right font-mono">
                {{ formatDuration(stats?.groupBehavior.treatment.durationPerView ?? 0) }}
              </td>
              <td class="px-4 py-3 text-right font-mono">
                {{ formatDuration(stats?.groupBehavior.control.durationPerView ?? 0) }}
              </td>
              <td class="px-4 py-3 text-center">
                <UBadge
                  v-if="betterGroup('durationPerView') === 'treatment'"
                  color="secondary"
                  variant="subtle"
                  size="xs"
                  >Nostalgia</UBadge
                >
                <UBadge
                  v-else-if="betterGroup('durationPerView') === 'control'"
                  color="neutral"
                  variant="subtle"
                  size="xs"
                  >Control</UBadge
                >
                <span v-else class="text-xs text-muted">—</span>
              </td>
            </tr>
            <tr>
              <td class="px-4 py-3">Positive Response Rate</td>
              <td class="px-4 py-3 text-right font-mono">
                {{ formatPct(stats?.groupBehavior.treatment.positiveResponseRate) }}
              </td>
              <td class="px-4 py-3 text-right font-mono">
                {{ formatPct(stats?.groupBehavior.control.positiveResponseRate) }}
              </td>
              <td class="px-4 py-3 text-center">
                <UBadge
                  v-if="betterGroup('positiveResponseRate') === 'treatment'"
                  color="secondary"
                  variant="subtle"
                  size="xs"
                  >Nostalgia</UBadge
                >
                <UBadge
                  v-else-if="betterGroup('positiveResponseRate') === 'control'"
                  color="neutral"
                  variant="subtle"
                  size="xs"
                  >Control</UBadge
                >
                <span v-else class="text-xs text-muted">—</span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </UCard>

    <!-- Stress Comparison -->
    <UCard>
      <template #header>
        <div class="flex items-center gap-2">
          <UIcon name="i-lucide-brain" class="text-xl text-purple-500" />
          <h2 class="text-lg font-semibold">Stress Level Comparison</h2>
          <UPopover mode="hover">
            <UIcon
              name="i-lucide-info"
              class="h-4 w-4 cursor-help text-muted hover:text-gray-600"
            />
            <template #content>
              <div class="space-y-1 p-2 text-xs">
                <p class="font-semibold text-gray-900 dark:text-white">Bucket Ranges:</p>
                <div class="grid grid-cols-[60px_1fr] gap-x-2 text-gray-600 dark:text-gray-300">
                  <span>Low:</span> <span class="font-mono">&lt; 0.33</span> <span>Medium:</span>
                  <span class="font-mono">0.33 - 0.66</span> <span>High:</span>
                  <span class="font-mono">&ge; 0.66</span>
                </div>
              </div>
            </template>
          </UPopover>
        </div>
      </template>

      <div class="grid gap-6 md:grid-cols-2">
        <!-- Nostalgia Group -->
        <div class="rounded-lg bg-amber-500/10 p-4">
          <h3 class="mb-3 font-semibold text-amber-600">Nostalgia Group</h3>
          <div class="space-y-2">
            <div class="flex items-center justify-between gap-2">
              <span class="text-sm">Average Stress</span>
              <span class="font-mono font-medium">
                {{ formatStress(stats?.stressComparison.treatment.avgStress) }}
              </span>
            </div>
            <div class="flex items-center justify-between gap-2">
              <span class="text-sm">Logs with Stress Data</span>
              <span class="font-medium">{{ stats?.stressComparison.treatment.logCount ?? 0 }}</span>
            </div>
            <div class="mt-3 flex gap-2">
              <div class="flex-1 rounded bg-green-500/20 p-2 text-center">
                <p class="text-xs text-muted">Low</p>
                <p class="font-bold text-green-600">
                  {{ comparison?.stressDistribution.treatment.low ?? 0 }}
                </p>
              </div>
              <div class="flex-1 rounded bg-yellow-500/20 p-2 text-center">
                <p class="text-xs text-muted">Medium</p>
                <p class="font-bold text-yellow-600">
                  {{ comparison?.stressDistribution.treatment.medium ?? 0 }}
                </p>
              </div>
              <div class="flex-1 rounded bg-red-500/20 p-2 text-center">
                <p class="text-xs text-muted">High</p>
                <p class="font-bold text-red-600">
                  {{ comparison?.stressDistribution.treatment.high ?? 0 }}
                </p>
              </div>
            </div>
          </div>
        </div>

        <!-- Control Group -->
        <div class="rounded-lg bg-slate-500/10 p-4">
          <h3 class="mb-3 font-semibold text-slate-600">Control Group</h3>
          <div class="space-y-2">
            <div class="flex items-center justify-between gap-2">
              <span class="text-sm">Average Stress</span>
              <span class="font-mono font-medium">
                {{ formatStress(stats?.stressComparison.control.avgStress) }}
              </span>
            </div>
            <div class="flex items-center justify-between gap-2">
              <span class="text-sm">Logs with Stress Data</span>
              <span class="font-medium">{{ stats?.stressComparison.control.logCount ?? 0 }}</span>
            </div>
            <div class="mt-3 flex gap-2">
              <div class="flex-1 rounded bg-green-500/20 p-2 text-center">
                <p class="text-xs text-muted">Low</p>
                <p class="font-bold text-green-600">
                  {{ comparison?.stressDistribution.control.low ?? 0 }}
                </p>
              </div>
              <div class="flex-1 rounded bg-yellow-500/20 p-2 text-center">
                <p class="text-xs text-muted">Medium</p>
                <p class="font-bold text-yellow-600">
                  {{ comparison?.stressDistribution.control.medium ?? 0 }}
                </p>
              </div>
              <div class="flex-1 rounded bg-red-500/20 p-2 text-center">
                <p class="text-xs text-muted">High</p>
                <p class="font-bold text-red-600">
                  {{ comparison?.stressDistribution.control.high ?? 0 }}
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </UCard>

    <!-- Emotion Comparison -->
    <UCard>
      <template #header>
        <div class="flex items-center gap-2">
          <UIcon name="i-lucide-smile" class="text-xl text-pink-500" />
          <h2 class="text-lg font-semibold">Emotion Distribution</h2>
        </div>
      </template>

      <div v-if="allEmotions.length === 0" class="py-8 text-center text-muted">
        No emotion data available yet
      </div>

      <div v-else class="overflow-x-auto">
        <table class="w-full text-sm">
          <thead>
            <tr class="border-b">
              <th class="py-2 text-left font-medium">Emotion</th>
              <th class="py-2 text-right font-medium text-amber-600">
                <span class="hidden sm:inline">Nostalgia</span>
                <span class="sm:hidden">Grp A</span>
              </th>
              <th class="py-2 text-right font-medium text-slate-600">
                <span class="hidden sm:inline">Control</span>
                <span class="sm:hidden">Grp B</span>
              </th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="emotion in allEmotions" :key="emotion" class="border-b border-default">
              <td class="py-2">{{ emotion }}</td>
              <td class="py-2 text-right font-mono">
                {{ comparison?.emotions.treatment[emotion] ?? 0 }}
              </td>
              <td class="py-2 text-right font-mono">
                {{ comparison?.emotions.control[emotion] ?? 0 }}
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </UCard>

    <!-- Completion & Feedback -->
    <div class="grid gap-6 md:grid-cols-2">
      <!-- Habit Completion -->
      <UCard>
        <template #header>
          <div class="flex items-center gap-2">
            <UIcon name="i-lucide-check-circle" class="text-xl text-green-500" />
            <h2 class="text-lg font-semibold">Habit Completion</h2>
          </div>
        </template>

        <div class="space-y-4">
          <div class="flex items-center justify-between rounded-lg bg-amber-500/10 p-3">
            <span class="font-medium text-amber-600">Nostalgia</span>
            <div class="text-right">
              <span class="text-2xl font-bold">
                {{ formatPct(stats?.completionComparison.treatment.rate) }}
              </span>
              <p class="text-xs text-muted">
                {{ stats?.completionComparison.treatment.completed ?? 0 }} /
                {{ stats?.completionComparison.treatment.total ?? 0 }} logs
              </p>
            </div>
          </div>
          <div class="flex items-center justify-between rounded-lg bg-slate-500/10 p-3">
            <span class="font-medium text-slate-600">Control</span>
            <div class="text-right">
              <span class="text-2xl font-bold">
                {{ formatPct(stats?.completionComparison.control.rate) }}
              </span>
              <p class="text-xs text-muted">
                {{ stats?.completionComparison.control.completed ?? 0 }} /
                {{ stats?.completionComparison.control.total ?? 0 }} logs
              </p>
            </div>
          </div>
        </div>
      </UCard>

      <!-- Nostalgia Feedback -->
      <UCard>
        <template #header>
          <div class="flex items-center gap-2">
            <UIcon name="i-lucide-sparkles" class="text-xl text-amber-500" />
            <h2 class="text-lg font-semibold">Nostalgia Feedback</h2>
          </div>
        </template>

        <div class="space-y-4">
          <div class="text-center">
            <p class="text-sm text-muted">Positive Response Rate</p>
            <p class="text-4xl font-bold text-amber-500">
              {{ formatPct(stats?.nostalgiaFeedback.positiveRate) }}
            </p>
          </div>
          <div class="flex justify-center gap-8">
            <div class="text-center">
              <p class="text-2xl font-bold text-green-500">
                {{ stats?.nostalgiaFeedback.positive ?? 0 }}
              </p>
              <p class="text-xs text-muted">"Brings back memories"</p>
            </div>
            <div class="text-center">
              <p class="text-2xl font-bold text-slate-400">
                {{
                  (stats?.nostalgiaFeedback.total ?? 0) - (stats?.nostalgiaFeedback.positive ?? 0)
                }}
              </p>
              <p class="text-xs text-muted">"Not really"</p>
            </div>
          </div>
        </div>
      </UCard>
    </div>
  </UContainer>
</template>
