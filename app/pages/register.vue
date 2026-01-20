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
    name: 'name',
    type: 'text',
    label: 'Name',
    placeholder: 'Enter your name',
    required: true,
  },
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
  {
    name: 'confirmPassword',
    label: 'Confirm Password',
    type: 'password',
    placeholder: 'Confirm your password',
    required: true,
  },
]

const schema = z
  .object({
    name: z.string({ message: 'Name is required' }).min(2, 'Name must be at least 2 characters'),
    email: z.email('Invalid email address'),
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

async function onSubmit(payload: FormSubmitEvent<Schema>) {
  try {
    loading.value = true

    const { error: _error } = await authClient.signUp.email({
      email: payload.data.email,
      password: payload.data.password,
      name: payload.data.name,
      fetchOptions: {
        onError(error) {
          toast.add({
            title: 'Sign up failed',
            description: error instanceof Error ? error.message : 'Could not create account',
            color: 'error',
          })
        },
        async onSuccess() {
          toast.add({
            title: 'Account created!',
            description: 'Welcome to our platform',
            color: 'success',
          })
        },
      },
    })

    // refresh their session
    await authClient.getSession()

    await useAuthStore().init()

    await navigateTo('/onboarding')
  } catch {
    toast.add({
      title: 'Sign up failed',
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
    <UAuthForm
      :schema="schema"
      :fields="fields"
      :loading="loading"
      title="Create account"
      description="Sign up to get started"
      icon="i-lucide-user-plus"
      @submit="onSubmit"
    >
      <template #description>
        Already have an account?
        <ULink
          :to="{
            path: '/login',
            query: route.query.redirectTo ? { redirectTo: route.query.redirectTo } : {},
          }"
          class="font-medium text-primary"
          >Sign in</ULink
        >
      </template>
    </UAuthForm>
  </UPageCard>
</template>
