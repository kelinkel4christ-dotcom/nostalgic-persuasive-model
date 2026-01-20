<script setup lang="ts">
export type ExperimentGroup = 'treatment' | 'control'

const emit = defineEmits<{
  next: [group: ExperimentGroup]
}>()

const selectedGroup = ref<ExperimentGroup | null>(null)

const groups = [
  {
    id: 'treatment' as ExperimentGroup,
    icon: 'i-lucide-sparkles',
    title: 'Nostalgia Group',
    subtitle: 'Personalized recommendations from your past',
    description:
      'Receive movie and music recommendations from your childhood and teen years to help with habit formation',
    gradient: 'from-amber-500 to-orange-600',
    bgGradient: 'from-amber-500/10 to-orange-600/10',
    borderColor: 'border-amber-500',
    iconColor: 'text-amber-500',
  },
  {
    id: 'control' as ExperimentGroup,
    icon: 'i-lucide-users',
    title: 'Control Group',
    subtitle: 'Standard habit tracking experience',
    description: 'Focus on habit tracking without personalized content recommendations',
    gradient: 'from-slate-500 to-gray-600',
    bgGradient: 'from-slate-500/10 to-gray-600/10',
    borderColor: 'border-slate-500',
    iconColor: 'text-slate-500',
  },
]

function selectGroup(group: ExperimentGroup) {
  selectedGroup.value = group
}

function handleNext() {
  if (selectedGroup.value) {
    emit('next', selectedGroup.value)
  }
}
</script>

<template>
  <div class="space-y-8">
    <!-- Header -->
    <div class="text-center">
      <div
        class="mx-auto mb-6 flex h-20 w-20 items-center justify-center rounded-full bg-gradient-to-br from-purple-500/20 to-indigo-600/20"
      >
        <UIcon name="i-lucide-flask-conical" class="h-10 w-10 text-purple-500" />
      </div>
      <h2
        class="bg-gradient-to-r from-purple-500 to-indigo-600 bg-clip-text text-2xl font-bold text-transparent"
      >
        Choose Your Study Group
      </h2>
      <p class="mt-2 text-gray-500 dark:text-gray-400">
        This research compares two approaches to habit formation
      </p>
    </div>

    <!-- Group Cards -->
    <div class="space-y-4">
      <button
        v-for="group in groups"
        :key="group.id"
        class="group relative w-full overflow-hidden rounded-2xl border-2 p-6 text-left transition-all duration-300 hover:scale-[1.02]"
        :class="[
          selectedGroup === group.id
            ? `${group.borderColor} bg-gradient-to-r ${group.bgGradient}`
            : 'border-gray-200 bg-white hover:border-gray-300 dark:border-gray-700 dark:bg-gray-800/50 dark:hover:border-gray-600',
        ]"
        @click="selectGroup(group.id)"
      >
        <!-- Selection Indicator -->
        <div
          v-if="selectedGroup === group.id"
          class="absolute top-4 right-4 flex h-6 w-6 items-center justify-center rounded-full bg-gradient-to-r"
          :class="group.gradient"
        >
          <UIcon name="i-lucide-check" class="h-4 w-4 text-white" />
        </div>

        <div class="flex items-start gap-4">
          <!-- Icon -->
          <div
            class="flex h-14 w-14 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br transition-transform duration-300 group-hover:scale-110"
            :class="group.bgGradient"
          >
            <UIcon :name="group.icon" class="h-7 w-7" :class="group.iconColor" />
          </div>

          <!-- Content -->
          <div class="flex-1 space-y-1">
            <h3 class="font-semibold text-gray-900 dark:text-white">
              {{ group.title }}
            </h3>
            <p class="text-sm font-medium" :class="group.iconColor">
              {{ group.subtitle }}
            </p>
            <p class="text-xs text-gray-500 dark:text-gray-400">
              {{ group.description }}
            </p>
          </div>
        </div>
      </button>
    </div>

    <!-- Continue Button -->
    <div class="pt-4">
      <UButton
        block
        size="lg"
        color="primary"
        class="bg-gradient-to-r from-purple-500 to-indigo-600 font-semibold hover:from-purple-600 hover:to-indigo-700"
        :disabled="!selectedGroup"
        @click="handleNext"
      >
        Continue
        <UIcon name="i-lucide-arrow-right" class="ml-2 h-4 w-4" />
      </UButton>
    </div>
  </div>
</template>
