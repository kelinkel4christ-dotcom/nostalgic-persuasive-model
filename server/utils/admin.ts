import type { H3Event } from 'h3'

/**
 * Check if the request has valid admin session.
 * Throws 401 if not authenticated.
 */
export function requireAdmin(event: H3Event): void {
  const adminSession = getCookie(event, 'admin_session')

  if (adminSession !== 'authenticated') {
    throw createError({
      statusCode: 401,
      message: 'Admin authentication required',
    })
  }
}
