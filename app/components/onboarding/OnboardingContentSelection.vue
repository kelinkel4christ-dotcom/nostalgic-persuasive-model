<script setup lang="ts">
import { useDebounceFn, onClickOutside } from '@vueuse/core'

interface MovieItem {
  id: number
  title: string
  year: number | null
  genres: string[] | null
}

interface SongItem {
  id: string
  name: string
  albumName: string | null
  artists: string[] | null
  year: number | null
  genre: string | null
}

const props = defineProps<{
  periodStart: number
  periodEnd: number
}>()

const emit = defineEmits<{
  next: [content: { movieIds: number[]; songIds: string[] }]
}>()

const REQUIRED_COUNT = 5

// Active tab
const activeTab = ref<'movies' | 'songs'>('movies')

// Content state
const displayedMovies = ref<MovieItem[]>([])
const displayedSongs = ref<SongItem[]>([])
const selectedMovieIds = ref<Set<number>>(new Set())
const selectedSongIds = ref<Set<string>>(new Set())

// Search state
const searchQuery = ref('')
const searchResults = ref<MovieItem[] | SongItem[]>([])
const isSearching = ref(false)
const showSearchDropdown = ref(false)
const searchContainerRef = ref<HTMLElement | null>(null)

// Loading states
const loadingMovies = ref(false)
const loadingSongs = ref(false)

// Click outside handler
onClickOutside(searchContainerRef, () => {
  showSearchDropdown.value = false
})

// Computed
const selectedMovies = computed(() =>
  displayedMovies.value.filter((m) => selectedMovieIds.value.has(m.id))
)

const selectedSongs = computed(() =>
  displayedSongs.value.filter((s) => selectedSongIds.value.has(s.id))
)

const movieCount = computed(() => selectedMovieIds.value.size)
const songCount = computed(() => selectedSongIds.value.size)
const canContinue = computed(
  () => movieCount.value >= REQUIRED_COUNT && songCount.value >= REQUIRED_COUNT
)

// Fetch functions
async function fetchMovies(mode: 'random' | 'popular' | 'similar' = 'random') {
  loadingMovies.value = true
  try {
    const selectedIds = Array.from(selectedMovieIds.value)
    const response = await $fetch('/api/content/movies', {
      query: {
        yearStart: props.periodStart,
        yearEnd: props.periodEnd,
        limit: 10,
        excludeIds: selectedIds.join(','),
        mode: mode,
        selectedIds: mode === 'similar' ? selectedIds.join(',') : undefined,
      },
    })
    displayedMovies.value = [
      ...displayedMovies.value.filter((m) => selectedMovieIds.value.has(m.id)),
      ...response.items.filter((m: MovieItem) => !selectedMovieIds.value.has(m.id)),
    ]
  } finally {
    loadingMovies.value = false
  }
}

async function fetchSongs(mode: 'random' | 'popular' | 'similar' = 'random') {
  loadingSongs.value = true
  try {
    const selectedIds = Array.from(selectedSongIds.value)
    const response = await $fetch('/api/content/songs', {
      query: {
        yearStart: props.periodStart,
        yearEnd: props.periodEnd,
        limit: 10,
        excludeIds: selectedIds.join(','),
        mode: mode,
        selectedIds: mode === 'similar' ? selectedIds.join(',') : undefined,
      },
    })
    displayedSongs.value = [
      ...displayedSongs.value.filter((s) => selectedSongIds.value.has(s.id)),
      ...response.items.filter((s: SongItem) => !selectedSongIds.value.has(s.id)),
    ]
  } finally {
    loadingSongs.value = false
  }
}

// Search function
async function performSearch(query: string) {
  if (!query.trim()) {
    searchResults.value = []
    showSearchDropdown.value = false
    return
  }

  isSearching.value = true
  try {
    const endpoint = activeTab.value === 'movies' ? '/api/content/movies' : '/api/content/songs'
    const response = await $fetch(endpoint, {
      query: {
        yearStart: props.periodStart,
        yearEnd: props.periodEnd,
        search: query,
        limit: 50,
      },
    })
    searchResults.value = response.items
    showSearchDropdown.value = true
  } finally {
    isSearching.value = false
  }
}

const debouncedSearch = useDebounceFn(performSearch, 300)

// Watch search query
watch(searchQuery, (query) => {
  if (query.trim()) {
    debouncedSearch(query)
  } else {
    searchResults.value = []
    showSearchDropdown.value = false
  }
})

// Clear search when switching tabs
watch(activeTab, () => {
  searchQuery.value = ''
  searchResults.value = []
  showSearchDropdown.value = false
})

// Toggle selection from grid
function toggleMovie(movie: MovieItem) {
  if (selectedMovieIds.value.has(movie.id)) {
    selectedMovieIds.value.delete(movie.id)
  } else if (selectedMovieIds.value.size < REQUIRED_COUNT) {
    selectedMovieIds.value.add(movie.id)
    // Ensure movie is in displayedMovies for tracking
    if (!displayedMovies.value.find((m) => m.id === movie.id)) {
      displayedMovies.value.push(movie)
    }
  }
  // Trigger reactivity
  selectedMovieIds.value = new Set(selectedMovieIds.value)
}

function toggleSong(song: SongItem) {
  if (selectedSongIds.value.has(song.id)) {
    selectedSongIds.value.delete(song.id)
  } else if (selectedSongIds.value.size < REQUIRED_COUNT) {
    selectedSongIds.value.add(song.id)
    // Ensure song is in displayedSongs for tracking
    if (!displayedSongs.value.find((s) => s.id === song.id)) {
      displayedSongs.value.push(song)
    }
  }
  // Trigger reactivity
  selectedSongIds.value = new Set(selectedSongIds.value)
}

// Add from search
function addFromSearch(item: MovieItem | SongItem) {
  if (activeTab.value === 'movies') {
    const movie = item as MovieItem
    if (!selectedMovieIds.value.has(movie.id) && selectedMovieIds.value.size < REQUIRED_COUNT) {
      selectedMovieIds.value.add(movie.id)
      selectedMovieIds.value = new Set(selectedMovieIds.value)
      if (!displayedMovies.value.find((m) => m.id === movie.id)) {
        displayedMovies.value.push(movie)
      }
    }
  } else {
    const song = item as SongItem
    if (!selectedSongIds.value.has(song.id) && selectedSongIds.value.size < REQUIRED_COUNT) {
      selectedSongIds.value.add(song.id)
      selectedSongIds.value = new Set(selectedSongIds.value)
      if (!displayedSongs.value.find((s) => s.id === song.id)) {
        displayedSongs.value.push(song)
      }
    }
  }
  searchQuery.value = ''
  showSearchDropdown.value = false
}

// Refresh displayed items - smart mode based on selection state
function refreshItems() {
  if (activeTab.value === 'movies') {
    // If movies selected, show similar movies; otherwise popular
    const mode = selectedMovieIds.value.size > 0 ? 'similar' : 'popular'
    fetchMovies(mode)
  } else {
    // If songs selected, show similar; otherwise popular songs
    const mode = selectedSongIds.value.size > 0 ? 'similar' : 'popular'
    fetchSongs(mode)
  }
}

function handleNext() {
  emit('next', {
    movieIds: Array.from(selectedMovieIds.value),
    songIds: Array.from(selectedSongIds.value),
  })
}

// Initial load
onMounted(() => {
  fetchMovies()
  fetchSongs()
})
</script>

<template>
  <div class="space-y-6">
    <!-- Header -->
    <div class="text-center">
      <div
        class="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-gradient-to-br from-amber-500/20 to-orange-600/20"
      >
        <UIcon name="i-lucide-heart" class="h-8 w-8 text-amber-500" />
      </div>
      <h2
        class="bg-gradient-to-r from-amber-500 to-orange-600 bg-clip-text text-xl font-bold text-transparent"
      >
        Pick your favorites
      </h2>
      <p class="mt-1 text-sm text-gray-500 dark:text-gray-400">
        Select {{ REQUIRED_COUNT }} movies and {{ REQUIRED_COUNT }} songs from your nostalgic era
      </p>
    </div>

    <!-- Tab Buttons -->
    <div class="flex overflow-hidden rounded-lg border border-gray-200 dark:border-gray-700">
      <button
        class="flex flex-1 items-center justify-center gap-2 py-2.5 text-sm font-medium transition-all"
        :class="
          activeTab === 'movies'
            ? 'bg-red-500 text-white'
            : 'bg-white text-gray-600 hover:bg-gray-50 dark:bg-gray-800 dark:text-gray-300 dark:hover:bg-gray-700'
        "
        @click="activeTab = 'movies'"
      >
        <UIcon name="i-lucide-film" class="h-4 w-4" />
        Movies
        <span
          class="rounded-full px-2 py-0.5 text-xs font-semibold"
          :class="
            activeTab === 'movies'
              ? 'bg-white/20 text-white'
              : movieCount >= REQUIRED_COUNT
                ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400'
                : 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400'
          "
        >
          {{ movieCount }}/{{ REQUIRED_COUNT }}
        </span>
      </button>
      <button
        class="flex flex-1 items-center justify-center gap-2 py-2.5 text-sm font-medium transition-all"
        :class="
          activeTab === 'songs'
            ? 'bg-green-500 text-white'
            : 'bg-white text-gray-600 hover:bg-gray-50 dark:bg-gray-800 dark:text-gray-300 dark:hover:bg-gray-700'
        "
        @click="activeTab = 'songs'"
      >
        <UIcon name="i-lucide-music" class="h-4 w-4" />
        Music
        <span
          class="rounded-full px-2 py-0.5 text-xs font-semibold"
          :class="
            activeTab === 'songs'
              ? 'bg-white/20 text-white'
              : songCount >= REQUIRED_COUNT
                ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400'
                : 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400'
          "
        >
          {{ songCount }}/{{ REQUIRED_COUNT }}
        </span>
      </button>
    </div>

    <!-- Search Bar with Dropdown -->
    <div ref="searchContainerRef" class="relative">
      <div class="flex gap-2">
        <div class="relative flex-1">
          <UIcon
            name="i-lucide-search"
            class="absolute top-1/2 left-3 h-4 w-4 -translate-y-1/2 text-gray-400"
          />
          <input
            v-model="searchQuery"
            type="text"
            :placeholder="activeTab === 'movies' ? 'Search movies...' : 'Search songs...'"
            class="w-full rounded-lg border border-gray-200 bg-white py-2.5 pr-4 pl-10 text-sm transition-colors placeholder:text-gray-400 focus:border-primary focus:ring-1 focus:ring-primary focus:outline-none dark:border-gray-700 dark:bg-gray-800 dark:text-white dark:placeholder:text-gray-500"
            @focus="searchQuery.trim() && (showSearchDropdown = true)"
          />
          <UIcon
            v-if="isSearching"
            name="i-lucide-loader-2"
            class="absolute top-1/2 right-3 h-4 w-4 -translate-y-1/2 animate-spin text-gray-400"
          />
        </div>
        <button
          class="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg border border-gray-200 bg-white transition-colors hover:bg-gray-50 dark:border-gray-700 dark:bg-gray-800 dark:hover:bg-gray-700"
          :disabled="activeTab === 'movies' ? loadingMovies : loadingSongs"
          title="Refresh suggestions"
          @click="refreshItems"
        >
          <UIcon
            name="i-lucide-refresh-cw"
            class="h-4 w-4 text-gray-600 dark:text-gray-400"
            :class="{ 'animate-spin': activeTab === 'movies' ? loadingMovies : loadingSongs }"
          />
        </button>
      </div>

      <!-- Search Results Dropdown -->
      <Transition
        enter-active-class="transition duration-100 ease-out"
        enter-from-class="opacity-0 scale-95"
        enter-to-class="opacity-100 scale-100"
        leave-active-class="transition duration-75 ease-in"
        leave-from-class="opacity-100 scale-100"
        leave-to-class="opacity-0 scale-95"
      >
        <div
          v-if="showSearchDropdown && searchResults.length > 0"
          class="absolute right-12 left-0 z-50 mt-1 max-h-60 overflow-y-auto rounded-lg border border-gray-200 bg-white shadow-lg dark:border-gray-700 dark:bg-gray-800"
        >
          <button
            v-for="item in searchResults"
            :key="activeTab === 'movies' ? (item as MovieItem).id : (item as SongItem).id"
            class="flex w-full items-center gap-3 px-3 py-2 text-left transition-colors hover:bg-gray-50 dark:hover:bg-gray-700"
            :class="{
              'opacity-50':
                activeTab === 'movies'
                  ? selectedMovieIds.has((item as MovieItem).id)
                  : selectedSongIds.has((item as SongItem).id),
            }"
            @click="addFromSearch(item)"
          >
            <div
              class="flex h-8 w-8 shrink-0 items-center justify-center rounded"
              :class="
                activeTab === 'movies'
                  ? 'bg-red-100 dark:bg-red-900/30'
                  : 'bg-green-100 dark:bg-green-900/30'
              "
            >
              <UIcon
                :name="activeTab === 'movies' ? 'i-lucide-film' : 'i-lucide-music'"
                class="h-4 w-4"
                :class="activeTab === 'movies' ? 'text-red-500' : 'text-green-500'"
              />
            </div>
            <div class="min-w-0 flex-1">
              <p class="truncate text-sm font-medium text-gray-900 dark:text-white">
                {{ activeTab === 'movies' ? (item as MovieItem).title : (item as SongItem).name }}
              </p>
              <p class="truncate text-xs text-gray-500 dark:text-gray-400">
                {{
                  activeTab === 'movies'
                    ? (item as MovieItem).year
                    : (item as SongItem).artists?.join(', ')
                }}
              </p>
            </div>
            <UIcon
              v-if="
                activeTab === 'movies'
                  ? selectedMovieIds.has((item as MovieItem).id)
                  : selectedSongIds.has((item as SongItem).id)
              "
              name="i-lucide-check"
              class="h-4 w-4 text-green-500"
            />
            <UIcon v-else name="i-lucide-plus" class="h-4 w-4 text-gray-400" />
          </button>
        </div>
      </Transition>
    </div>

    <!-- Selected Items Panel -->
    <div
      v-if="
        (activeTab === 'movies' && selectedMovies.length > 0) ||
        (activeTab === 'songs' && selectedSongs.length > 0)
      "
      class="rounded-lg border border-gray-200 bg-gray-50 p-3 dark:border-gray-700 dark:bg-gray-800/50"
    >
      <p class="mb-2 text-xs font-medium text-gray-500 dark:text-gray-400">
        Selected {{ activeTab === 'movies' ? 'Movies' : 'Songs' }}
      </p>
      <div class="flex flex-wrap gap-2">
        <template v-if="activeTab === 'movies'">
          <button
            v-for="movie in selectedMovies"
            :key="movie.id"
            class="flex items-center gap-1.5 rounded-full bg-red-100 py-1 pr-2 pl-3 text-xs font-medium text-red-700 transition-colors hover:bg-red-200 dark:bg-red-900/30 dark:text-red-400 dark:hover:bg-red-900/50"
            @click="toggleMovie(movie)"
          >
            <span class="max-w-32 truncate">{{ movie.title }}</span>
            <UIcon name="i-lucide-x" class="h-3 w-3" />
          </button>
        </template>
        <template v-else>
          <button
            v-for="song in selectedSongs"
            :key="song.id"
            class="flex items-center gap-1.5 rounded-full bg-green-100 py-1 pr-2 pl-3 text-xs font-medium text-green-700 transition-colors hover:bg-green-200 dark:bg-green-900/30 dark:text-green-400 dark:hover:bg-green-900/50"
            @click="toggleSong(song)"
          >
            <span class="max-w-32 truncate">{{ song.name }}</span>
            <UIcon name="i-lucide-x" class="h-3 w-3" />
          </button>
        </template>
      </div>
    </div>

    <!-- Content List (Single Column) -->
    <div class="max-h-64 space-y-2 overflow-y-auto">
      <!-- Movies List -->
      <template v-if="activeTab === 'movies'">
        <div
          v-if="loadingMovies && displayedMovies.length === 0"
          class="flex items-center justify-center py-8"
        >
          <UIcon name="i-lucide-loader-2" class="h-6 w-6 animate-spin text-gray-400" />
        </div>
        <button
          v-for="movie in displayedMovies.filter((m) => !selectedMovieIds.has(m.id))"
          :key="movie.id"
          class="flex w-full items-center gap-3 rounded-lg border border-gray-200 bg-white p-3 text-left transition-all hover:border-red-300 hover:bg-red-50/50 dark:border-gray-700 dark:bg-gray-800/50 dark:hover:border-red-700 dark:hover:bg-red-900/10"
          :disabled="selectedMovieIds.size >= REQUIRED_COUNT"
          @click="toggleMovie(movie)"
        >
          <div
            class="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-red-100 dark:bg-red-900/30"
          >
            <UIcon name="i-lucide-film" class="h-5 w-5 text-red-500" />
          </div>
          <div class="min-w-0 flex-1">
            <p class="font-medium text-gray-900 dark:text-white">{{ movie.title }}</p>
            <p class="text-sm text-gray-500 dark:text-gray-400">
              {{ movie.genres?.slice(0, 3).join(' • ') || 'Unknown genre' }}
              <span v-if="movie.year" class="text-gray-400"> • {{ movie.year }}</span>
            </p>
          </div>
          <UIcon
            name="i-lucide-plus"
            class="h-5 w-5 shrink-0 text-gray-400"
            :class="{ 'opacity-30': selectedMovieIds.size >= REQUIRED_COUNT }"
          />
        </button>
      </template>

      <!-- Songs List -->
      <template v-else>
        <div
          v-if="loadingSongs && displayedSongs.length === 0"
          class="flex items-center justify-center py-8"
        >
          <UIcon name="i-lucide-loader-2" class="h-6 w-6 animate-spin text-gray-400" />
        </div>
        <button
          v-for="song in displayedSongs.filter((s) => !selectedSongIds.has(s.id))"
          :key="song.id"
          class="flex w-full items-center gap-3 rounded-lg border border-gray-200 bg-white p-3 text-left transition-all hover:border-green-300 hover:bg-green-50/50 dark:border-gray-700 dark:bg-gray-800/50 dark:hover:border-green-700 dark:hover:bg-green-900/10"
          :disabled="selectedSongIds.size >= REQUIRED_COUNT"
          @click="toggleSong(song)"
        >
          <div
            class="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-green-100 dark:bg-green-900/30"
          >
            <UIcon name="i-lucide-music" class="h-5 w-5 text-green-500" />
          </div>
          <div class="min-w-0 flex-1">
            <p class="font-medium text-gray-900 dark:text-white">{{ song.name }}</p>
            <p class="text-sm text-gray-500 dark:text-gray-400">
              {{ song.artists?.slice(0, 2).join(', ') || 'Unknown artist' }}
              <span v-if="song.year" class="text-gray-400"> • {{ song.year }}</span>
            </p>
          </div>
          <UIcon
            name="i-lucide-plus"
            class="h-5 w-5 shrink-0 text-gray-400"
            :class="{ 'opacity-30': selectedSongIds.size >= REQUIRED_COUNT }"
          />
        </button>
      </template>
    </div>

    <!-- Continue Button -->
    <div class="pt-2">
      <UButton
        block
        size="lg"
        color="primary"
        class="bg-gradient-to-r from-amber-500 to-orange-600 font-semibold hover:from-amber-600 hover:to-orange-700"
        :disabled="!canContinue"
        @click="handleNext"
      >
        <template v-if="!canContinue">
          Select {{ REQUIRED_COUNT - movieCount }} more movies &
          {{ REQUIRED_COUNT - songCount }} more songs
        </template>
        <template v-else>
          Continue
          <UIcon name="i-lucide-arrow-right" class="ml-2 h-4 w-4" />
        </template>
      </UButton>
    </div>
  </div>
</template>
