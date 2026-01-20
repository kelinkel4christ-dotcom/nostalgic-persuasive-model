<script setup lang="ts">
const links = [
  {
    label: 'Dashboard',
    icon: 'i-lucide-layout-dashboard',
    to: '/',
  },
  {
    label: 'Settings',
    icon: 'i-lucide-settings',
    to: '/settings',
  },
]
</script>

<template>
  <div class="min-h-screen bg-gray-50 dark:bg-gray-900">
    <header
      data-tutorial="app-header"
      class="sticky top-0 z-50 w-full border-b border-gray-200 bg-white/75 backdrop-blur dark:border-gray-800 dark:bg-gray-900/75"
    >
      <UContainer>
        <div class="flex h-16 items-center justify-between gap-4">
          <div class="flex items-center gap-4">
            <ULink to="/" class="flex items-center gap-2 text-xl font-bold text-primary">
              <div class="rounded-lg bg-primary/10 p-1.5">
                <UIcon name="i-lucide-layers" class="h-6 w-6 text-primary" />
              </div>
              <span class="hidden sm:inline-block">Nostalgic</span>
            </ULink>

            <nav class="ml-4 hidden items-center gap-1 md:flex">
              <UButton
                v-for="link in links"
                :key="link.to"
                :to="link.to"
                variant="ghost"
                color="neutral"
                :icon="link.icon"
              >
                {{ link.label }}
              </UButton>
            </nav>
          </div>

          <div class="flex items-center gap-2">
            <!-- Mobile Navigation -->
            <UButton
              v-for="link in links"
              :key="link.to"
              :to="link.to"
              variant="ghost"
              color="neutral"
              :icon="link.icon"
              class="md:hidden"
            />

            <UColorModeButton />

            <UButton
              to="/logout"
              variant="ghost"
              color="neutral"
              icon="i-lucide-log-out"
              label="Sign out"
            />
          </div>
        </div>
      </UContainer>
    </header>

    <main class="py-8">
      <slot />
    </main>

    <footer class="border-t border-gray-200 bg-white py-6 dark:border-gray-800 dark:bg-gray-900">
      <UContainer>
        <div
          class="flex flex-col items-center justify-between gap-4 text-center md:flex-row md:text-left"
        >
          <p class="text-sm text-gray-500 dark:text-gray-400">
            &copy; {{ new Date().getFullYear() }} Nostalgic Inc. All rights reserved.
          </p>
          <div class="flex items-center gap-4 text-sm text-gray-500 dark:text-gray-400">
            <ULink to="#" class="hover:text-primary">Privacy Policy</ULink>
            <ULink to="#" class="hover:text-primary">Terms of Service</ULink>
          </div>
        </div>
      </UContainer>
    </footer>
  </div>
</template>
