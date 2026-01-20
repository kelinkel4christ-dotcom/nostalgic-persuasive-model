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
    name: 'email',
    type: 'email',
    label: 'Email',
    placeholder: 'Enter your email',
    required: true,
  },
  {
    name: 'password',
    label: 'Password',
    type: 'password',
    placeholder: 'Enter your password',
    required: true,
  },
]

const schema = z.object({
  email: z.email('Invalid email address'),
  password: z
    .string({ message: 'Password is required' })
    .min(8, 'Password must be at least 8 characters'),
})

type Schema = z.output<typeof schema>

const loading = ref(false)

async function onSubmit(payload: FormSubmitEvent<Schema>) {
  try {
    loading.value = true

    const { data: _data, error: _error } = await authClient.signIn.email({
      email: payload.data.email,
      password: payload.data.password,
      fetchOptions: {
        onError(error) {
          toast.add({
            title: 'Sign in failed',
            description: error instanceof Error ? error.message : 'Invalid email or password',
            color: 'error',
          })
        },
        onSuccess() {
          toast.add({
            title: 'Welcome back!',
            description: 'You have been signed in successfully',
            color: 'success',
          })

          const redirectPath = (route.query.redirectTo as string) || '/'
          navigateTo(redirectPath)
        },
      },
    })
  } catch (error) {
    toast.add({
      title: 'Sign in failed',
      description: error instanceof Error ? error.message : 'An unexpected error occurred',
      color: 'error',
    })
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <UPageCard class="w-full">
    <UAuthForm
      :schema="schema"
      :fields="fields"
      :loading="loading"
      title="Welcome back"
      description="Enter your credentials to access your account"
      icon="i-lucide-lock"
      @submit="onSubmit"
    >
      <template #description>
        Don't have an account?
        <ULink
          :to="{
            path: '/register',
            query: route.query.redirectTo ? { redirectTo: route.query.redirectTo } : {},
          }"
          class="font-medium text-primary"
          >Sign up</ULink
        >
      </template>
      <template #password-hint>
        <ULink to="/forgot-password" class="font-medium text-primary" tabindex="-1"
          >Forgot password?</ULink
        >
      </template>
    </UAuthForm>
  </UPageCard>
</template>
