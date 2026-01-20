import { db } from '~~/server/utils/db'
import { user } from '~~/server/database/schema'
import { eq } from 'drizzle-orm'
import { requireAuth } from '~~/server/utils/session'

export default defineEventHandler(async (event) => {
  const authUser = await requireAuth(event)

  const body = await readBody<{ name?: string }>(event)

  if (!body.name || body.name.trim().length === 0) {
    throw createError({
      statusCode: 400,
      message: 'Name is required',
    })
  }

  if (body.name.length > 100) {
    throw createError({
      statusCode: 400,
      message: 'Name must be less than 100 characters',
    })
  }

  await db.update(user).set({ name: body.name.trim() }).where(eq(user.id, authUser.id))

  return { success: true, name: body.name.trim() }
})
