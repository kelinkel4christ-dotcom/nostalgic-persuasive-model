<script setup lang="ts">
import { computed } from 'vue'

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
}>()

// Filter and sort logs
const chartData = computed(() => {
  return props.logs
    .filter((log) => log.stressLevel !== null && log.stressLevel !== undefined)
    .sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime())
    .map((log) => ({
      ...log,
      stress: log.stressLevel ?? 0,
      parsedDate: new Date(log.date),
      // Capitalize emotion
      emotionLabel: log.emotion
        ? log.emotion.charAt(0).toUpperCase() + log.emotion.slice(1)
        : 'Neutral',
    }))
})

// Dimensions (SVG coordinate space)
const width = 800
const height = 300
const padding = { top: 40, right: 40, bottom: 30, left: 40 } // Increased top padding for emojis
const chartWidth = width - padding.left - padding.right
const chartHeight = height - padding.top - padding.bottom

// Scales
const getX = (index: number) => {
  if (chartData.value.length <= 1) return padding.left + chartWidth / 2
  return padding.left + (index / (chartData.value.length - 1)) * chartWidth
}

const getY = (stress: number) => {
  return padding.top + chartHeight - stress * chartHeight
}

// Path generator
const linePath = computed(() => {
  if (chartData.value.length === 0) return ''
  return 'M ' + chartData.value.map((d, i) => `${getX(i)} ${getY(d.stress)}`).join(' L ')
})

const areaPath = computed(() => {
  if (chartData.value.length === 0) return ''
  let d = `M ${getX(0)} ${padding.top + chartHeight}`
  chartData.value.forEach((point, i) => {
    d += ` L ${getX(i)} ${getY(point.stress)}`
  })
  d += ` L ${getX(chartData.value.length - 1)} ${padding.top + chartHeight} Z`
  return d
})

const formatDate = (date: Date) => {
  return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
}

// Switched to potentially safer emojis
const emotionsList = [
  { name: 'Joy', emoji: '😄', color: 'text-yellow-500' }, // Switched from 😊
  { name: 'Sadness', emoji: '😢', color: 'text-blue-500' },
  { name: 'Anger', emoji: '😡', color: 'text-red-500' }, // Switched from 😠
  { name: 'Fear', emoji: '😱', color: 'text-purple-500' }, // Switched from 😨
  { name: 'Love', emoji: '🥰', color: 'text-pink-500' },
  { name: 'Surprise', emoji: '😲', color: 'text-orange-500' },
  { name: 'Neutral', emoji: '😐', color: 'text-gray-500' },
]

const getEmotionEmoji = (emotion: string | null | undefined): string => {
  if (!emotion) return '😐'
  const found = emotionsList.find((e) => e.name.toLowerCase() === emotion.toLowerCase())
  return found ? found.emoji : '😐'
}
</script>

<template>
  <UCard data-tutorial="stress-chart" class="w-full overflow-hidden">
    <template #header>
      <div class="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div class="flex items-center gap-2">
          <div class="rounded-lg bg-primary/10 p-2 text-primary">
            <UIcon name="i-lucide-activity" class="text-xl" />
          </div>
          <div>
            <h3 class="font-semibold text-gray-900 dark:text-white">Stress & Emotion History</h3>
            <p class="text-sm text-gray-500">Last {{ chartData.length }} Days</p>
          </div>
        </div>
        <div class="hidden text-xs text-gray-500 sm:block">Combined analysis of daily logs</div>
      </div>
    </template>

    <div v-if="chartData.length > 1" class="relative">
      <!-- Scrollable Chart Container -->
      <div class="relative w-full overflow-x-auto pb-4">
        <!-- Constraint Container -->
        <div class="relative min-w-[600px]" :style="{ aspectRatio: `${width}/${height}` }">
          <!-- SVG Layer (Background Lines) -->
          <svg :viewBox="`0 0 ${width} ${height}`" class="absolute inset-0 h-full w-full">
            <defs>
              <linearGradient id="lineGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stop-color="rgb(59, 130, 246)" stop-opacity="0.3" />
                <stop offset="100%" stop-color="rgb(59, 130, 246)" stop-opacity="0.0" />
              </linearGradient>
            </defs>

            <!-- Grid Lines -->
            <g v-for="tick in [0, 0.25, 0.5, 0.75, 1]" :key="tick">
              <line
                :x1="padding.left"
                :y1="getY(tick)"
                :x2="width - padding.right"
                :y2="getY(tick)"
                stroke="currentColor"
                class="text-gray-100 dark:text-gray-800"
                stroke-width="1"
              />
            </g>

            <!-- Area & Line -->
            <path :d="areaPath" fill="url(#lineGradient)" />
            <path
              :d="linePath"
              fill="none"
              stroke="rgb(59, 130, 246)"
              stroke-width="2"
              stroke-linecap="round"
              stroke-linejoin="round"
            />
          </svg>

          <!-- HTML Overlay Layer (Interactivity) -->
          <div class="pointer-events-none absolute inset-0 top-0 left-0 h-full w-full">
            <div
              v-for="(point, i) in chartData"
              :key="point.id"
              class="group pointer-events-auto absolute flex flex-col items-center"
              :style="{
                left: `${(getX(i) / width) * 100}%`,
                top: `${(getY(point.stress) / height) * 100}%`,
                transform: 'translate(-50%, -50%)', // Center on point
                width: '40px', // Hit area
                height: '40px',
              }"
            >
              <!-- The Dot (Visual Only) -->
              <div class="relative flex items-center justify-center">
                <!-- Outer Glow (Hover) -->
                <div
                  class="absolute inset-0 scale-50 rounded-full bg-primary/20 opacity-0 transition-all duration-300 group-hover:scale-150 group-hover:opacity-100"
                />
                <!-- Circle -->
                <div
                  class="h-3 w-3 rounded-full border-2 border-primary bg-white shadow-sm transition-transform group-hover:scale-110 dark:bg-gray-900"
                />
              </div>

              <!-- Tooltip on Emoji -->
              <div class="absolute bottom-6 left-1/2 -translate-x-1/2">
                <UTooltip
                  :text="`${formatDate(point.parsedDate)} • ${Math.round(point.stress * 100)}% Stress • ${getEmotionEmoji(point.emotion)} ${point.emotionLabel}`"
                  :popper="{ arrow: true, placement: 'top' }"
                  :delay-duration="0"
                >
                  <div class="cursor-help text-lg transition-transform select-none hover:scale-125">
                    {{ getEmotionEmoji(point.emotion) }}
                  </div>
                </UTooltip>
              </div>
            </div>

            <!-- X-Axis Labels -->
            <div
              v-for="(point, i) in chartData"
              :key="`label-${point.id}`"
              class="absolute text-[10px] text-gray-400 select-none"
              :style="{
                left: `${(getX(i) / width) * 100}%`,
                bottom: '5px',
                transform: 'translateX(-50%)',
              }"
            >
              {{ formatDate(point.parsedDate) }}
            </div>
          </div>
        </div>
      </div>

      <!-- Legend -->
      <div
        class="border-t border-gray-100 bg-gray-50/50 p-6 dark:border-gray-800 dark:bg-gray-900/50"
      >
        <h4 class="mb-3 text-xs font-semibold tracking-wider text-gray-500 uppercase">
          Emotion Key
        </h4>
        <div class="flex flex-wrap gap-x-6 gap-y-3">
          <div v-for="e in emotionsList" :key="e.name" class="flex items-center gap-2 text-sm">
            <span class="text-lg leading-none">{{ e.emoji }}</span>
            <span class="text-gray-700 dark:text-gray-300">{{ e.name }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Empty State -->
    <div v-else class="flex flex-col items-center justify-center py-12 text-center">
      <UIcon name="i-lucide-bar-chart-2" class="mb-4 text-4xl text-gray-300" />
      <h3 class="font-medium text-gray-900 dark:text-white">Not enough data</h3>
      <p class="mt-1 text-sm text-gray-500">Log more days to see your history.</p>
    </div>
  </UCard>
</template>
