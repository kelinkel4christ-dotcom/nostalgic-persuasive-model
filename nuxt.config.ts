// https://nuxt.com/docs/api/configuration/nuxt-config
export default defineNuxtConfig({
  compatibilityDate: '2025-07-15',
  devtools: { enabled: true },

  modules: [
    '@nuxt/eslint',
    '@nuxt/hints',
    '@nuxt/image',
    '@nuxt/ui',
    '@pinia/nuxt',
    'pinia-plugin-persistedstate/nuxt',
    '@vueuse/nuxt',
  ],
  css: ['~/assets/css/main.css'],
  ignore: ['/tests', '/training', '/fastapi-backend', '/models', '/logs', '/dataset'],

  runtimeConfig: {
    // Server-only config (not exposed to client)
    fastApiUrl: process.env.FASTAPI_URL || 'http://localhost:8000',
  },
})
