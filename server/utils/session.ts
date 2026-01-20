import type { H3Event } from 'h3'
import { auth } from './auth'

export const requireAuth = async (event: H3Event) => {
  const session = await auth.api.getSession({ headers: event.headers })

  if (!session?.user) {
    throw createError({ statusCode: 401, statusMessage: 'Unauthorized' })
  }

  // Set the context and return the user for convenience
  event.context.user = session.user
  return session.user
}
