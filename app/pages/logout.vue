<script setup lang="ts">
import { authClient } from '~/utils/auth-client'

definePageMeta({
  auth: true,
})

const toast = useToast()

onMounted(async () => {
  try {
    await authClient.signOut()
    toast.add({
      title: 'Signed out',
      description: 'You have been signed out successfully',
      color: 'success',
    })
  } catch {
    toast.add({
      title: 'Sign out failed',
      description: 'An unexpected error occurred',
      color: 'error',
    })
  } finally {
    await navigateTo('/login')
  }
})
</script>

<template>
  <div class="flex min-h-screen items-center justify-center">
    <div class="text-center">
      <UIcon name="i-lucide-loader-2" class="mx-auto h-8 w-8 animate-spin" />
      <p class="text-muted-foreground mt-4">Signing out...</p>
    </div>
  </div>
</template>
