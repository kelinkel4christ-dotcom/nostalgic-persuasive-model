import { z } from 'zod'

const bodySchema = z.object({
  email: z.string(),
  password: z.string(),
})

// Hardcoded admin credentials
const ADMIN_EMAIL = 'admin'
const ADMIN_PASSWORD = 'admin'

export default defineEventHandler(async (event) => {
  const body = await readValidatedBody(event, bodySchema.parse)

  // Check admin credentials
  if (body.email !== ADMIN_EMAIL || body.password !== ADMIN_PASSWORD) {
    throw createError({
      statusCode: 401,
      message: 'Invalid admin credentials',
    })
  }

  // Set admin session cookie
  setCookie(event, 'admin_session', 'authenticated', {
    httpOnly: true,
    secure: process.env.NODE_ENV === 'production',
    sameSite: 'lax',
    maxAge: 60 * 60 * 24, // 24 hours
    path: '/',
  })

  return { success: true }
})
