export default defineNuxtRouteMiddleware((to) => {
  const authStore = useAuthStore()

  // If the route has 'auth: false' in its meta, skip the check
  if (to.meta.auth === false) {
    return
  }

  // Otherwise, check if user is logged in
  if (!authStore.user) {
    return navigateTo({
      path: '/login',
      query: {
        redirectTo: to.path,
      },
    })
  }
})
