<script setup lang="ts">
import * as z from 'zod'
import type { FormSubmitEvent, AuthFormField } from '@nuxt/ui'
import { authClient } from '~/utils/auth-client'

definePageMeta({
  auth: false,
  layout: 'auth',
})

const route = useRoute()
const toast = useToast()

const fields: AuthFormField[] = [
  {
    name: 'password',
    label: 'New Password',
    type: 'password',
    placeholder: 'Enter your new password',
    required: true,
  },
  {
    name: 'confirmPassword',
    label: 'Confirm New Password',
    type: 'password',
    placeholder: 'Confirm your new password',
    required: true,
  },
]

const schema = z
  .object({
    password: z
      .string({ message: 'Password is required' })
      .min(8, 'Password must be at least 8 characters'),
    confirmPassword: z.string({ message: 'Confirm password is required' }),
  })
  .refine((data) => data.password === data.confirmPassword, {
    message: 'Passwords do not match',
    path: ['confirmPassword'],
  })

type Schema = z.output<typeof schema>

const loading = ref(false)
const token = computed(() => route.query.token as string)
const valid = ref(false)

onMounted(async () => {
  if (!token.value) {
    toast.add({
      title: 'Invalid reset link',
      description: 'The reset link is invalid or has expired',
      color: 'error',
    })
    await navigateTo('/forgot-password')
    return
  }

  try {
    const { error } = await authClient.getPasswordResetToken({
      token: token.value,
    })

    if (error) {
      toast.add({
        title: 'Invalid reset link',
        description: 'The reset link is invalid or has expired',
        color: 'error',
      })
      await navigateTo('/forgot-password')
      return
    }

    valid.value = true
  } catch {
    toast.add({
      title: 'Invalid reset link',
      description: 'The reset link is invalid or has expired',
      color: 'error',
    })
    await navigateTo('/forgot-password')
  }
})

async function onSubmit(payload: FormSubmitEvent<Schema>) {
  if (!token.value) return

  try {
    loading.value = true

    const { error } = await authClient.resetPassword({
      token: token.value,
      password: payload.data.password,
    })

    if (error) {
      toast.add({
        title: 'Password reset failed',
        description: error.message || 'Could not reset password',
        color: 'error',
      })
      return
    }

    toast.add({
      title: 'Password reset successful',
      description: 'You can now sign in with your new password',
      color: 'success',
    })

    await navigateTo('/login')
  } catch {
    toast.add({
      title: 'Password reset failed',
      description: 'An unexpected error occurred',
      color: 'error',
    })
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <UPageCard class="w-full">
    <template v-if="valid">
      <UAuthForm
        :schema="schema"
        :fields="fields"
        :loading="loading"
        title="Reset password"
        description="Enter your new password"
        icon="i-lucide-lock-open"
        @submit="onSubmit"
      />
    </template>
    <div v-else class="flex justify-center py-8">
      <UIcon name="i-lucide-loader-2" class="h-8 w-8 animate-spin" />
    </div>
  </UPageCard>
</template>
