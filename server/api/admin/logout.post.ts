export default defineEventHandler(async (event) => {
  // Clear admin session cookie
  deleteCookie(event, 'admin_session', { path: '/' })

  return { success: true }
})
