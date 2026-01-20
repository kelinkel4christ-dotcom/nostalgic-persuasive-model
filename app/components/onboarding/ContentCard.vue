<script setup lang="ts">
const props = defineProps<{
  type: 'movie' | 'song'
  item: {
    id: number | string
    title?: string
    name?: string
    year?: number | null
    genres?: string[] | null
    artists?: string[] | null
    genre?: string | null
    albumName?: string | null
  }
  selected: boolean
}>()

const emit = defineEmits<{
  toggle: []
}>()

const displayTitle = computed(() => props.item.title || props.item.name || 'Unknown')

const displaySubtitle = computed(() => {
  if (props.type === 'movie') {
    return props.item.genres?.slice(0, 3).join(' • ') || 'Unknown genre'
  }
  return props.item.artists?.slice(0, 2).join(', ') || 'Unknown artist'
})

const displayMeta = computed(() => {
  if (props.type === 'movie') {
    return props.item.year || ''
  }
  return props.item.genre || props.item.albumName || ''
})
</script>

<template>
  <button
    class="group relative w-full overflow-hidden rounded-xl border-2 p-4 text-left transition-all duration-200 hover:scale-[1.02]"
    :class="[
      selected
        ? type === 'movie'
          ? 'border-red-400 bg-red-50 dark:border-red-500 dark:bg-red-900/20'
          : 'border-green-400 bg-green-50 dark:border-green-500 dark:bg-green-900/20'
        : 'border-gray-200 bg-white hover:border-gray-300 dark:border-gray-700 dark:bg-gray-800/50 dark:hover:border-gray-600',
    ]"
    @click="emit('toggle')"
  >
    <!-- Selection Indicator -->
    <div
      v-if="selected"
      class="absolute top-3 right-3 flex h-6 w-6 items-center justify-center rounded-full"
      :class="type === 'movie' ? 'bg-red-500' : 'bg-green-500'"
    >
      <UIcon name="i-lucide-check" class="h-4 w-4 text-white" />
    </div>

    <div class="flex items-start gap-3">
      <!-- Icon -->
      <div
        class="flex h-12 w-12 shrink-0 items-center justify-center rounded-lg"
        :class="
          type === 'movie' ? 'bg-red-100 dark:bg-red-900/30' : 'bg-green-100 dark:bg-green-900/30'
        "
      >
        <UIcon
          :name="type === 'movie' ? 'i-lucide-film' : 'i-lucide-music'"
          class="h-6 w-6"
          :class="type === 'movie' ? 'text-red-500' : 'text-green-500'"
        />
      </div>

      <!-- Content -->
      <div class="min-w-0 flex-1">
        <h4 class="truncate font-medium text-gray-900 dark:text-white">
          {{ displayTitle }}
        </h4>
        <p class="mt-0.5 truncate text-sm text-gray-500 dark:text-gray-400">
          {{ displaySubtitle }}
        </p>
        <p v-if="displayMeta" class="mt-1 text-xs text-gray-400 dark:text-gray-500">
          {{ displayMeta }}
        </p>
      </div>
    </div>
  </button>
</template>
