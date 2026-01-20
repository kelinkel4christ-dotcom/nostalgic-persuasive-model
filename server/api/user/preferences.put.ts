import { db } from '~~/server/utils/db'
import { userPreferences } from '~~/server/database/schema'
import { eq } from 'drizzle-orm'
import { requireAuth } from '~~/server/utils/session'
import { z } from 'zod'

const updatePreferencesSchema = z
  .object({
    nostalgicPeriodStart: z.number().int().min(1920).max(2100).optional(),
    nostalgicPeriodEnd: z.number().int().min(1920).max(2100).optional(),
  })
  .refine(
    (data) => {
      if (data.nostalgicPeriodStart && data.nostalgicPeriodEnd) {
        return data.nostalgicPeriodStart <= data.nostalgicPeriodEnd
      }
      return true
    },
    {
      message: 'End year must be after start year',
      path: ['nostalgicPeriodEnd'],
    }
  )

export default defineEventHandler(async (event) => {
  const authUser = await requireAuth(event)
  const body = await readBody(event)

  const result = updatePreferencesSchema.safeParse(body)
  if (!result.success) {
    throw createError({
      statusCode: 400,
      message: 'Invalid input',
      data: result.error.issues,
    })
  }

  const { nostalgicPeriodStart, nostalgicPeriodEnd } = result.data

  const updateData: {
    nostalgicPeriodStart?: number
    nostalgicPeriodEnd?: number
  } = {}
  if (nostalgicPeriodStart !== undefined) updateData.nostalgicPeriodStart = nostalgicPeriodStart
  if (nostalgicPeriodEnd !== undefined) updateData.nostalgicPeriodEnd = nostalgicPeriodEnd

  if (Object.keys(updateData).length === 0) {
    return { success: true, message: 'No changes provided' }
  }

  // Update preferences
  // Note: We don't check experimentGroup here strictly, allowing updates if the user is somehow in control but hitting this endpoint.
  // The UI will control visibility.

  await db.update(userPreferences).set(updateData).where(eq(userPreferences.userId, authUser.id))

  return { success: true, preferences: updateData }
})
