<script setup lang="ts">
definePageMeta({
  layout: 'auth',
  auth: false,
})

const toast = useToast()
const router = useRouter()

const email = ref('')
const password = ref('')
const loading = ref(false)

async function handleLogin() {
  if (!email.value || !password.value) {
    toast.add({ title: 'Please enter email and password', color: 'error' })
    return
  }

  loading.value = true
  try {
    await $fetch('/api/admin/login', {
      method: 'POST',
      body: { email: email.value, password: password.value },
    })
    router.push('/admin')
  } catch {
    toast.add({ title: 'Invalid admin credentials', color: 'error' })
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="space-y-6">
    <!-- Header -->
    <div class="text-center">
      <div
        class="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-linear-to-br from-rose-500/20 to-pink-600/20"
      >
        <UIcon name="i-lucide-shield" class="h-8 w-8 text-rose-500" />
      </div>
      <h1 class="text-2xl font-bold">Admin Login</h1>
      <p class="mt-1 text-sm text-muted">Research dashboard access</p>
    </div>

    <!-- Form -->
    <form class="space-y-4" @submit.prevent="handleLogin">
      <div>
        <label class="mb-2 block text-sm font-medium">Email</label>
        <UInput
          v-model="email"
          placeholder="admin"
          size="lg"
          class="w-full"
          autocomplete="username"
        />
      </div>

      <div>
        <label class="mb-2 block text-sm font-medium">Password</label>
        <UInput
          v-model="password"
          type="password"
          placeholder="••••••••"
          size="lg"
          class="w-full"
          autocomplete="current-password"
        />
      </div>

      <UButton
        type="submit"
        color="primary"
        size="lg"
        block
        :loading="loading"
        class="bg-linear-to-r from-rose-500 to-pink-600"
      >
        Sign In
      </UButton>
    </form>

    <div class="text-center">
      <NuxtLink to="/login" class="text-sm text-muted hover:text-primary">
        ← Back to user login
      </NuxtLink>
    </div>
  </div>
</template>
