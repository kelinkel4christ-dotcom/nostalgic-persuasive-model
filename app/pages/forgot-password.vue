<script setup lang="ts">
import * as z from 'zod'
import type { FormSubmitEvent, AuthFormField } from '@nuxt/ui'
import { authClient } from '~/utils/auth-client'

definePageMeta({
  auth: false,
  layout: 'auth',
})

const toast = useToast()

const fields: AuthFormField[] = [
  {
    name: 'email',
    type: 'email',
    label: 'Email',
    placeholder: 'Enter your email',
    required: true,
  },
]

const schema = z.object({
  email: z.email('Invalid email address'),
})

type Schema = z.output<typeof schema>

const loading = ref(false)
const sent = ref(false)

async function onSubmit(payload: FormSubmitEvent<Schema>) {
  try {
    loading.value = true

    const { error } = await authClient.requestPasswordReset({
      email: payload.data.email,
      redirectTo: `${window.location.origin}/reset-password`,
    })

    if (error) {
      toast.add({
        title: 'Failed to send reset link',
        description: error.message || 'Could not send password reset email',
        color: 'error',
      })
      return
    }

    sent.value = true
    toast.add({
      title: 'Reset link sent',
      description: 'Check your email for a password reset link',
      color: 'success',
    })
  } catch {
    toast.add({
      title: 'Failed to send reset link',
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
    <template v-if="!sent">
      <UAuthForm
        :schema="schema"
        :fields="fields"
        :loading="loading"
        title="Forgot password?"
        description="Enter your email to receive a password reset link"
        icon="i-lucide-key"
        @submit="onSubmit"
      >
        <template #description>
          Remember your password?
          <ULink to="/login" class="font-medium text-primary">Sign in</ULink>
        </template>
      </UAuthForm>
    </template>
    <div v-else class="space-y-4 text-center">
      <div class="flex justify-center">
        <div class="rounded-full bg-green-100 p-4 dark:bg-green-900/20">
          <UIcon name="i-lucide-mail-check" class="h-12 w-12 text-green-600 dark:text-green-400" />
        </div>
      </div>
      <div>
        <h2 class="text-2xl font-semibold">Check your email</h2>
        <p class="text-muted-foreground mt-2">
          We've sent a password reset link to your email. The link will expire in 1 hour.
        </p>
      </div>
      <UButton to="/login" variant="ghost" block> Back to sign in </UButton>
    </div>
  </UPageCard>
</template>
