import { authClient } from '~/utils/auth-client'

export const useAuthStore = defineStore('useAuthStore', () => {
  const session = ref<Awaited<ReturnType<typeof authClient.useSession>> | null>(null)

  async function init() {
    const data = await authClient.useSession(useFetch)
    session.value = data
  }

  const user = computed(() => session.value?.data?.user)
  const loading = computed(() => session.value?.isPending)

  return {
    init,
    user,
    loading,
  }
})
