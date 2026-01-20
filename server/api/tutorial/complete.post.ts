import { db } from '~~/server/utils/db'
import { userPreferences } from '~~/server/database/schema'
import { requireAuth } from '~~/server/utils/session'
import { eq } from 'drizzle-orm'

export default defineEventHandler(async (event) => {
  const user = await requireAuth(event)

  await db
    .update(userPreferences)
    .set({
      tutorialCompletedAt: new Date(),
      tutorialSkippedAt: null,
    })
    .where(eq(userPreferences.userId, user.id))

  return {
    success: true,
  }
})
