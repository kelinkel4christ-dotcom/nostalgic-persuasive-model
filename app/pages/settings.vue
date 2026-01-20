<script setup lang="ts">
import { authClient } from '~/utils/auth-client'

definePageMeta({
  layout: 'default',
})

const authStore = useAuthStore()
const toast = useToast()

// Profile form state
const profileName = ref('')
const profileLoading = ref(false)

// Delete account state
const showDeleteModal = ref(false)
const deletePassword = ref('')
const deleteLoading = ref(false)

// Preferences data - API returns { preferences, onboardingComplete }
interface UserPreferencesResponse {
  preferences: {
    birthYear: number | null
    nostalgicPeriodStart: number | null
    nostalgicPeriodEnd: number | null
    habitType: 'exercise' | 'smoking_cessation'
    experimentGroup: 'treatment' | 'control'
    researchConsent: boolean
  } | null
  onboardingComplete: boolean
}

const {
  data: preferencesData,
  status: preferencesStatus,
  refresh: refreshPreferences,
} = await useFetch<UserPreferencesResponse>('/api/habits/preferences', { lazy: true })

// Computed to access preferences
const preferences = computed(() => preferencesData.value?.preferences)

// Nostalgic Period Editing
const isEditingPeriod = ref(false)
const editStartYear = ref(0)
const editEndYear = ref(0)
const editPeriodLoading = ref(false)

// Generate year options
const startYearOptions = computed(() => {
  const years = []
  const minYear = preferences.value?.birthYear || 1960
  const maxYear = new Date().getFullYear() - 1
  for (let year = minYear; year <= maxYear; year++) {
    years.push({ label: year.toString(), value: year })
  }
  return years
})

const endYearOptions = computed(() => {
  const years = []
  const minYear = editStartYear.value
  const maxYear = new Date().getFullYear() - 1
  for (let year = minYear; year <= maxYear; year++) {
    years.push({ label: year.toString(), value: year })
  }
  return years
})

// Initialize edit values when entering edit mode
watch(isEditingPeriod, (isEditing) => {
  if (isEditing && preferences.value) {
    editStartYear.value =
      preferences.value.nostalgicPeriodStart ||
      (preferences.value.birthYear ? preferences.value.birthYear + 5 : 1990)
    editEndYear.value =
      preferences.value.nostalgicPeriodEnd ||
      (preferences.value.birthYear ? preferences.value.birthYear + 19 : 2005)
  }
})

async function saveNostalgicPeriod() {
  if (editEndYear.value < editStartYear.value) {
    toast.add({ title: 'End year must be after start year', color: 'error' })
    return
  }

  editPeriodLoading.value = true
  try {
    await $fetch('/api/user/preferences', {
      method: 'PUT',
      body: {
        nostalgicPeriodStart: editStartYear.value,
        nostalgicPeriodEnd: editEndYear.value,
      },
    })

    await refreshPreferences()
    isEditingPeriod.value = false
    toast.add({ title: 'Nostalgic period updated', color: 'success' })
  } catch (error: unknown) {
    toast.add({
      title: 'Failed to update period',
      description: error instanceof Error ? error.message : 'An error occurred',
      color: 'error',
    })
  } finally {
    editPeriodLoading.value = false
  }
}

// Initialize form with current user data
watchEffect(() => {
  if (authStore.user?.name) {
    profileName.value = authStore.user.name
  }
})

// Format date for display
function formatDate(date: Date | string | undefined): string {
  if (!date) return 'Unknown'
  return new Date(date).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  })
}

// Save profile changes
async function saveProfile() {
  if (!profileName.value.trim()) {
    toast.add({ title: 'Name is required', color: 'error' })
    return
  }

  profileLoading.value = true
  try {
    await $fetch('/api/user/profile', {
      method: 'PATCH',
      body: { name: profileName.value.trim() },
    })
    await authStore.init() // Refresh user data
    toast.add({ title: 'Profile updated successfully', color: 'success' })
  } catch {
    toast.add({ title: 'Failed to update profile', color: 'error' })
  } finally {
    profileLoading.value = false
  }
}

// Delete account
async function deleteAccount() {
  if (!deletePassword.value) {
    toast.add({ title: 'Please enter your password', color: 'error' })
    return
  }

  deleteLoading.value = true
  try {
    await authClient.deleteUser({
      password: deletePassword.value,
      fetchOptions: {
        onSuccess: () => {
          navigateTo('/login')
        },
        onError: (ctx) => {
          toast.add({
            title: 'Failed to delete account',
            description: ctx.error.message || 'Invalid password',
            color: 'error',
          })
        },
      },
    })
  } catch {
    toast.add({ title: 'Failed to delete account', color: 'error' })
  } finally {
    deleteLoading.value = false
    showDeleteModal.value = false
    deletePassword.value = ''
  }
}

// Habit type label
const habitTypeLabel = computed(() => {
  if (!preferences.value) return ''
  return preferences.value.habitType === 'exercise' ? 'Exercise & Fitness' : 'Smoking Cessation'
})
</script>

<template>
  <UContainer class="py-8">
    <div class="mx-auto max-w-2xl">
      <!-- Page Header -->
      <div class="mb-8">
        <h1 class="text-2xl font-bold sm:text-3xl">Settings</h1>
        <p class="mt-1 text-muted">Manage your account and preferences</p>
      </div>

      <!-- Profile Section -->
      <UCard class="mb-6">
        <template #header>
          <div class="flex items-center gap-2">
            <UIcon name="i-lucide-user" class="text-xl text-primary" />
            <h2 class="text-lg font-semibold">Profile</h2>
          </div>
        </template>

        <div class="space-y-6">
          <!-- Name -->
          <div>
            <label class="mb-2 block text-sm font-medium">Display Name</label>
            <UInput v-model="profileName" placeholder="Your name" size="lg" class="w-full" />
          </div>

          <!-- Email (read-only) -->
          <div>
            <label class="mb-2 block text-sm font-medium">Email</label>
            <UInput :model-value="authStore.user?.email || ''" disabled size="lg" class="w-full" />
            <p class="mt-1.5 text-xs text-muted">Email cannot be changed</p>
          </div>

          <!-- Member Since -->
          <div>
            <label class="mb-2 block text-sm font-medium">Member Since</label>
            <p class="text-sm text-muted">
              {{ formatDate(authStore.user?.createdAt) }}
            </p>
          </div>

          <!-- Save Button -->
          <div class="flex justify-end pt-2">
            <UButton
              color="primary"
              :loading="profileLoading"
              :disabled="profileName === authStore.user?.name"
              @click="saveProfile"
            >
              Save Changes
            </UButton>
          </div>
        </div>
      </UCard>

      <!-- Preferences Section -->
      <UCard class="mb-6">
        <template #header>
          <div class="flex items-center gap-2">
            <UIcon name="i-lucide-settings-2" class="text-xl text-primary" />
            <h2 class="text-lg font-semibold">Preferences</h2>
          </div>
        </template>

        <div v-if="preferencesStatus === 'pending'" class="flex justify-center py-8">
          <UIcon name="i-lucide-loader-2" class="animate-spin text-2xl text-muted" />
        </div>

        <div v-else-if="preferences" class="space-y-4">
          <!-- Experiment Group -->
          <div class="flex flex-col gap-1 sm:flex-row sm:items-center sm:justify-between">
            <span class="text-sm font-medium">Study Group</span>
            <UBadge
              :color="preferences.experimentGroup === 'treatment' ? 'warning' : 'neutral'"
              variant="subtle"
            >
              {{ preferences.experimentGroup === 'treatment' ? 'Nostalgia' : 'Control' }}
            </UBadge>
          </div>

          <!-- Birth Year (treatment only) -->
          <div
            v-if="preferences.experimentGroup === 'treatment' && preferences.birthYear"
            class="flex flex-col gap-1 sm:flex-row sm:items-center sm:justify-between"
          >
            <span class="text-sm font-medium">Birth Year</span>
            <span class="text-sm text-muted">{{ preferences.birthYear }}</span>
          </div>

          <!-- Nostalgic Period (treatment only) -->
          <div
            v-if="preferences.experimentGroup === 'treatment'"
            class="flex flex-col gap-1 border-b border-gray-100 pb-4 last:border-0 last:pb-0 sm:flex-row sm:items-start sm:justify-between dark:border-gray-800"
          >
            <div class="py-1">
              <span class="block text-sm font-medium">Nostalgic Period</span>
              <p class="text-xs text-muted">The era that brings you joy</p>
            </div>

            <div v-if="!isEditingPeriod" class="flex items-center gap-3">
              <span class="text-sm font-medium">
                {{ preferences.nostalgicPeriodStart }} - {{ preferences.nostalgicPeriodEnd }}
              </span>
              <UButton
                size="xs"
                variant="ghost"
                color="primary"
                icon="i-lucide-pencil"
                @click="isEditingPeriod = true"
              >
                Edit
              </UButton>
            </div>

            <div
              v-else
              class="flex flex-col items-end gap-3 rounded-lg bg-gray-50 p-3 sm:w-96 dark:bg-gray-800/50"
            >
              <div class="flex w-full flex-col gap-3 sm:flex-row sm:items-center">
                <div class="flex flex-1 items-center gap-2">
                  <label class="text-xs font-medium text-muted">From</label>
                  <USelectMenu
                    v-model="editStartYear"
                    :items="startYearOptions"
                    value-key="value"
                    size="md"
                    class="flex-1"
                  />
                </div>
                <div class="flex flex-1 items-center gap-2">
                  <label class="text-xs font-medium text-muted">To</label>
                  <USelectMenu
                    v-model="editEndYear"
                    :items="endYearOptions"
                    value-key="value"
                    size="md"
                    class="flex-1"
                  />
                </div>
              </div>

              <div class="flex gap-2">
                <UButton
                  size="xs"
                  variant="ghost"
                  color="neutral"
                  :disabled="editPeriodLoading"
                  @click="isEditingPeriod = false"
                >
                  Cancel
                </UButton>
                <UButton
                  size="xs"
                  color="primary"
                  :loading="editPeriodLoading"
                  @click="saveNostalgicPeriod"
                >
                  Save
                </UButton>
              </div>
            </div>
          </div>

          <!-- Habit Type -->
          <div class="flex flex-col gap-1 sm:flex-row sm:items-center sm:justify-between">
            <span class="text-sm font-medium">Habit Goal</span>
            <UBadge
              :color="preferences.habitType === 'exercise' ? 'success' : 'info'"
              variant="subtle"
            >
              {{ habitTypeLabel }}
            </UBadge>
          </div>

          <!-- Research Consent -->
          <div class="flex flex-col gap-1 sm:flex-row sm:items-center sm:justify-between">
            <span class="text-sm font-medium">Research Consent</span>
            <UBadge :color="preferences.researchConsent ? 'success' : 'neutral'" variant="subtle">
              {{ preferences.researchConsent ? 'Opted In' : 'Opted Out' }}
            </UBadge>
          </div>
        </div>

        <div v-else class="py-4 text-center text-muted">
          <p>No preferences found. Please complete onboarding.</p>
          <UButton to="/onboarding" color="primary" variant="soft" class="mt-2">
            Complete Onboarding
          </UButton>
        </div>
      </UCard>

      <!-- Danger Zone -->
      <UCard class="border-red-500/30 bg-red-500/5">
        <template #header>
          <div class="flex items-center gap-2">
            <UIcon name="i-lucide-alert-triangle" class="text-xl text-red-500" />
            <h2 class="text-lg font-semibold text-red-500">Danger Zone</h2>
          </div>
        </template>

        <div class="space-y-4">
          <div>
            <h3 class="font-medium">Delete Account</h3>
            <p class="mt-1 text-sm text-muted">
              Permanently delete your account and all associated data. This action cannot be undone.
            </p>
          </div>

          <UButton color="error" variant="soft" @click="showDeleteModal = true">
            Delete My Account
          </UButton>
        </div>
      </UCard>
    </div>

    <!-- Delete Confirmation Modal -->
    <UModal v-model:open="showDeleteModal">
      <template #content>
        <div class="p-6">
          <div class="mb-4 flex items-center gap-3">
            <div
              class="flex h-12 w-12 items-center justify-center rounded-full bg-red-100 dark:bg-red-900/30"
            >
              <UIcon name="i-lucide-trash-2" class="text-2xl text-red-500" />
            </div>
            <div>
              <h3 class="text-lg font-semibold">Delete Account</h3>
              <p class="text-sm text-muted">This action is permanent</p>
            </div>
          </div>

          <p class="mb-4 text-sm">
            All your data including habit logs, preferences, and feedback will be permanently
            deleted. Enter your password to confirm.
          </p>

          <UInput
            v-model="deletePassword"
            type="password"
            placeholder="Enter your password"
            size="lg"
            class="mb-4 w-full"
          />

          <div class="flex gap-3">
            <UButton
              color="neutral"
              variant="outline"
              class="flex-1"
              @click="showDeleteModal = false"
            >
              Cancel
            </UButton>
            <UButton
              color="error"
              class="flex-1"
              :loading="deleteLoading"
              :disabled="!deletePassword"
              @click="deleteAccount"
            >
              Delete Account
            </UButton>
          </div>
        </div>
      </template>
    </UModal>
  </UContainer>
</template>
