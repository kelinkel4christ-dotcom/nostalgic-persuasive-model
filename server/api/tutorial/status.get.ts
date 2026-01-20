import { db } from '~~/server/utils/db'
import { userPreferences } from '~~/server/database/schema'
import { requireAuth } from '~~/server/utils/session'
import { eq } from 'drizzle-orm'

export default defineEventHandler(async (event) => {
  const user = await requireAuth(event)

  const prefs = await db.query.userPreferences.findFirst({
    where: eq(userPreferences.userId, user.id),
  })

  if (!prefs) {
    return {
      completed: false,
      skipped: false,
    }
  }

  return {
    completed: !!prefs.tutorialCompletedAt,
    skipped: !!prefs.tutorialSkippedAt,
  }
})
