export default defineNuxtPlugin(async () => {
  await useAuthStore().init()
})
