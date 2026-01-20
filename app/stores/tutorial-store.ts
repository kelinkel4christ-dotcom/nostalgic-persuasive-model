interface TutorialStep {
  id: string
  targetSelector: string
  title: string
  description: string
  position: 'top' | 'bottom' | 'left' | 'right' | 'center'
  highlightPadding: number
}

const treatmentSteps: TutorialStep[] = [
  {
    id: 'welcome',
    targetSelector: '[data-tutorial="app-header"]',
    title: 'Welcome to Your Habit Journey',
    description:
      "This application uses nostalgic memories to help you build healthier habits. Let's explore how it works!",
    position: 'bottom',
    highlightPadding: 20,
  },
  {
    id: 'today-status',
    targetSelector: '[data-tutorial="today-status"]',
    title: "Today's Goal",
    description:
      'Track your daily habit progress here. Log your completion and write a short journal entry.',
    position: 'right',
    highlightPadding: 16,
  },
  {
    id: 'recommendation',
    targetSelector: '[data-tutorial="recommendation-card"]',
    title: 'Your Nostalgic Content',
    description:
      'Daily personalized recommendations from your chosen era. Rate them to help us improve suggestions.',
    position: 'left',
    highlightPadding: 16,
  },
  {
    id: 'refresh-button',
    targetSelector: '[data-tutorial="refresh-button"]',
    title: 'Get a New Pick',
    description:
      "Not feeling this recommendation? Click 'New Pick' to get a different one from your nostalgic era.",
    position: 'bottom',
    highlightPadding: 8,
  },
  {
    id: 'open-content',
    targetSelector: '[data-tutorial="open-content-button"]',
    title: 'Enjoy the Content',
    description: 'Click to open the song on Spotify or search for the movie trailer on YouTube.',
    position: 'top',
    highlightPadding: 8,
  },
  {
    id: 'feedback',
    targetSelector: '[data-tutorial="feedback-buttons"]',
    title: 'Help Us Improve',
    description:
      'Tell us if this content brings back memories. Your feedback helps us recommend better content!',
    position: 'top',
    highlightPadding: 8,
  },
  {
    id: 'calendar',
    targetSelector: '[data-tutorial="habit-calendar"]',
    title: 'Habit Calendar',
    description: 'View your progress over time. Consistent logging builds lasting habits!',
    position: 'top',
    highlightPadding: 16,
  },
  {
    id: 'charts',
    targetSelector: '[data-tutorial="stress-chart"]',
    title: 'Your Wellness Insights',
    description: 'Track how your mood and stress levels change as you build your habit.',
    position: 'left',
    highlightPadding: 16,
  },
  {
    id: 'complete',
    targetSelector: '[data-tutorial="app-header"]',
    title: "You're All Set!",
    description:
      'Start logging daily and watch your habits grow. Use the "Take Tour" button anytime to revisit this guide.',
    position: 'bottom',
    highlightPadding: 20,
  },
]

const controlSteps: TutorialStep[] = [
  {
    id: 'welcome',
    targetSelector: '[data-tutorial="app-header"]',
    title: 'Welcome to Your Habit Journey',
    description:
      'This application helps you build healthier habits through daily tracking and insights. Let us show you around!',
    position: 'bottom',
    highlightPadding: 20,
  },
  {
    id: 'today-status',
    targetSelector: '[data-tutorial="today-status"]',
    title: "Today's Goal",
    description:
      'Track your daily habit progress here. Log your completion and write a short journal entry.',
    position: 'right',
    highlightPadding: 16,
  },
  {
    id: 'recommendation',
    targetSelector: '[data-tutorial="recommendation-card"]',
    title: 'Daily Content',
    description:
      'Enjoy a new song or movie recommendation each day. Rate them to help us improve suggestions.',
    position: 'left',
    highlightPadding: 16,
  },
  {
    id: 'refresh-button',
    targetSelector: '[data-tutorial="refresh-button"]',
    title: 'Get a New Pick',
    description: "Not feeling this recommendation? Click 'New Pick' to get a different one.",
    position: 'bottom',
    highlightPadding: 8,
  },
  {
    id: 'open-content',
    targetSelector: '[data-tutorial="open-content-button"]',
    title: 'Enjoy the Content',
    description: 'Click to open the song on Spotify or search for the movie trailer on YouTube.',
    position: 'top',
    highlightPadding: 8,
  },
  {
    id: 'feedback',
    targetSelector: '[data-tutorial="feedback-buttons"]',
    title: 'Help Us Improve',
    description:
      'Tell us if you enjoyed this content. Your feedback helps us recommend better picks!',
    position: 'top',
    highlightPadding: 8,
  },
  {
    id: 'calendar',
    targetSelector: '[data-tutorial="habit-calendar"]',
    title: 'Habit Calendar',
    description: 'View your progress over time. Consistent logging builds lasting habits!',
    position: 'top',
    highlightPadding: 16,
  },
  {
    id: 'charts',
    targetSelector: '[data-tutorial="stress-chart"]',
    title: 'Your Wellness Insights',
    description: 'Track how your mood and stress levels change as you build your habit.',
    position: 'left',
    highlightPadding: 16,
  },
  {
    id: 'complete',
    targetSelector: '[data-tutorial="app-header"]',
    title: "You're All Set!",
    description:
      'Start logging daily and watch your habits grow. Use the "Take Tour" button anytime to revisit this guide.',
    position: 'bottom',
    highlightPadding: 20,
  },
]

interface TutorialState {
  isActive: boolean
  currentStepIndex: number
  hasCompletedTutorial: boolean
  hasSkippedTutorial: boolean
  isLoading: boolean
  experimentGroup: 'treatment' | 'control'
}

export const useTutorialStore = defineStore('tutorial', {
  state: (): TutorialState => ({
    isActive: false,
    currentStepIndex: 0,
    hasCompletedTutorial: false,
    hasSkippedTutorial: false,
    isLoading: false,
    experimentGroup: 'treatment',
  }),

  getters: {
    tutorialSteps(state): TutorialStep[] {
      return state.experimentGroup === 'treatment' ? treatmentSteps : controlSteps
    },

    currentStep(state): TutorialStep | undefined {
      const steps = state.experimentGroup === 'treatment' ? treatmentSteps : controlSteps
      return steps[state.currentStepIndex]
    },

    isLastStep(state): boolean {
      const steps = state.experimentGroup === 'treatment' ? treatmentSteps : controlSteps
      return state.currentStepIndex === steps.length - 1
    },

    progress(state): number {
      const steps = state.experimentGroup === 'treatment' ? treatmentSteps : controlSteps
      return ((state.currentStepIndex + 1) / steps.length) * 100
    },

    showTakeTourButton(state): boolean {
      return !state.isActive && !state.hasCompletedTutorial && !state.isLoading
    },
  },

  actions: {
    async fetchTutorialStatus() {
      this.isLoading = true
      try {
        const data = await $fetch<{ completed: boolean; skipped: boolean }>('/api/tutorial/status')
        this.hasCompletedTutorial = data.completed
        this.hasSkippedTutorial = data.skipped
      } catch (error) {
        console.error('Failed to fetch tutorial status:', error)
      } finally {
        this.isLoading = false
      }
    },

    async startTour() {
      this.currentStepIndex = 0
      this.isActive = true
    },

    async restartTour() {
      this.currentStepIndex = 0
      this.hasSkippedTutorial = false
      this.isActive = true
      await this.markNotCompleted()
    },

    async nextStep() {
      const steps = this.experimentGroup === 'treatment' ? treatmentSteps : controlSteps
      if (this.currentStepIndex < steps.length - 1) {
        this.currentStepIndex++
      } else {
        await this.completeTutorial()
      }
    },

    async prevStep() {
      if (this.currentStepIndex > 0) {
        this.currentStepIndex--
      }
    },

    async goToStep(index: number) {
      const steps = this.experimentGroup === 'treatment' ? treatmentSteps : controlSteps
      if (index >= 0 && index < steps.length) {
        this.currentStepIndex = index
      }
    },

    async skipTutorial() {
      this.isActive = false
      this.hasSkippedTutorial = true
      try {
        await $fetch('/api/tutorial/skip', { method: 'POST' })
      } catch (error) {
        console.error('Failed to skip tutorial:', error)
      }
    },

    async completeTutorial() {
      this.isActive = false
      this.hasCompletedTutorial = true
      this.hasSkippedTutorial = false
      try {
        await $fetch('/api/tutorial/complete', { method: 'POST' })
      } catch (error) {
        console.error('Failed to complete tutorial:', error)
      }
    },

    async markNotCompleted() {
      try {
        await $fetch('/api/tutorial/status', { method: 'GET' })
      } catch (error) {
        console.error('Failed to reset tutorial status:', error)
      }
    },
  },
})
