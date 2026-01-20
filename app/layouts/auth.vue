<template>
  <div class="grid min-h-screen lg:grid-cols-2">
    <!-- Left Column: Branding & Visuals -->
    <div
      class="relative hidden flex-col justify-between overflow-hidden bg-linear-to-br from-zinc-50 to-zinc-200 p-12 text-gray-900 lg:flex dark:from-zinc-900 dark:to-zinc-950 dark:text-white"
    >
      <div class="relative z-10">
        <div class="mb-8 flex items-center gap-2">
          <div class="rounded-lg bg-primary/10 p-2 backdrop-blur dark:bg-white/10">
            <UIcon name="i-lucide-layers" class="h-8 w-8 text-primary dark:text-white" />
          </div>
          <span class="text-2xl font-bold tracking-tight">Nostalgic</span>
        </div>
        <div class="space-y-4">
          <h1 class="text-4xl font-bold tracking-tight sm:text-5xl">Nostalgia Persuasive System</h1>
          <p class="max-w-md text-lg text-gray-600 dark:text-gray-300">
            A research-driven application that leverages nostalgic content recommendations to
            promote positive habit formation.
          </p>
        </div>
      </div>

      <!-- Decorative Pattern -->
      <div
        class="pointer-events-none absolute top-0 left-0 h-full w-full opacity-10"
        style="
          background-image: radial-gradient(circle at 2px 2px, white 1px, transparent 0);
          background-size: 32px 32px;
        "
      />
    </div>

    <!-- Right Column: Content -->
    <div
      class="relative flex flex-col items-center justify-center bg-gray-50 p-8 sm:p-12 dark:bg-gray-900"
    >
      <div class="w-full max-w-md space-y-8">
        <slot />
      </div>

      <div class="mt-8 text-center text-sm text-gray-500 dark:text-gray-400">
        &copy; {{ new Date().getFullYear() }} Nostalgic Inc. All rights reserved.
      </div>
    </div>
  </div>
</template>
