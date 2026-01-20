<script setup lang="ts">
export type HabitType = 'exercise' | 'smoking_cessation'

const emit = defineEmits<{
  next: [habit: HabitType]
}>()

const selectedHabit = ref<HabitType | null>(null)

const habits = [
  {
    id: 'exercise' as HabitType,
    icon: 'i-lucide-dumbbell',
    title: 'Exercise & Fitness',
    subtitle: 'Stay consistent with your fitness routine',
    description:
      'Use nostalgic content to motivate you during workouts and celebrate your milestones',
    gradient: 'from-emerald-500 to-teal-600',
    bgGradient: 'from-emerald-500/10 to-teal-600/10',
    borderColor: 'border-emerald-500',
    iconColor: 'text-emerald-500',
  },
  {
    id: 'smoking_cessation' as HabitType,
    icon: 'i-lucide-cigarette-off',
    title: 'Quit Smoking',
    subtitle: 'Break free from smoking for good',
    description:
      'Nostalgic triggers help distract from cravings and reinforce your positive choices',
    gradient: 'from-rose-500 to-pink-600',
    bgGradient: 'from-rose-500/10 to-pink-600/10',
    borderColor: 'border-rose-500',
    iconColor: 'text-rose-500',
  },
]

function selectHabit(habit: HabitType) {
  selectedHabit.value = habit
}

function handleNext() {
  if (selectedHabit.value) {
    emit('next', selectedHabit.value)
  }
}
</script>

<template>
  <div class="space-y-8">
    <!-- Header -->
    <div class="text-center">
      <div
        class="mx-auto mb-6 flex h-20 w-20 items-center justify-center rounded-full bg-gradient-to-br from-blue-500/20 to-indigo-600/20"
      >
        <UIcon name="i-lucide-target" class="h-10 w-10 text-blue-500" />
      </div>
      <h2
        class="bg-gradient-to-r from-blue-500 to-indigo-600 bg-clip-text text-2xl font-bold text-transparent"
      >
        What's your goal?
      </h2>
      <p class="mt-2 text-gray-500 dark:text-gray-400">
        Choose the habit you want to build or break
      </p>
    </div>

    <!-- Habit Cards -->
    <div class="space-y-4">
      <button
        v-for="habit in habits"
        :key="habit.id"
        class="group relative w-full overflow-hidden rounded-2xl border-2 p-6 text-left transition-all duration-300 hover:scale-[1.02]"
        :class="[
          selectedHabit === habit.id
            ? `${habit.borderColor} bg-gradient-to-r ${habit.bgGradient}`
            : 'border-gray-200 bg-white hover:border-gray-300 dark:border-gray-700 dark:bg-gray-800/50 dark:hover:border-gray-600',
        ]"
        @click="selectHabit(habit.id)"
      >
        <!-- Selection Indicator -->
        <div
          v-if="selectedHabit === habit.id"
          class="absolute top-4 right-4 flex h-6 w-6 items-center justify-center rounded-full bg-gradient-to-r"
          :class="habit.gradient"
        >
          <UIcon name="i-lucide-check" class="h-4 w-4 text-white" />
        </div>

        <div class="flex items-start gap-4">
          <!-- Icon -->
          <div
            class="flex h-14 w-14 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br transition-transform duration-300 group-hover:scale-110"
            :class="habit.bgGradient"
          >
            <UIcon :name="habit.icon" class="h-7 w-7" :class="habit.iconColor" />
          </div>

          <!-- Content -->
          <div class="flex-1 space-y-1">
            <h3 class="font-semibold text-gray-900 dark:text-white">
              {{ habit.title }}
            </h3>
            <p class="text-sm font-medium" :class="habit.iconColor">
              {{ habit.subtitle }}
            </p>
            <p class="text-xs text-gray-500 dark:text-gray-400">
              {{ habit.description }}
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
        class="bg-gradient-to-r from-blue-500 to-indigo-600 font-semibold hover:from-blue-600 hover:to-indigo-700"
        :disabled="!selectedHabit"
        @click="handleNext"
      >
        Continue
        <UIcon name="i-lucide-arrow-right" class="ml-2 h-4 w-4" />
      </UButton>
    </div>
  </div>
</template>
