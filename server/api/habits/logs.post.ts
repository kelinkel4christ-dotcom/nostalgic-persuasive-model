import { db } from '~~/server/utils/db'
import { dailyHabitLogs } from '~~/server/database/schema'
import { eq, and } from 'drizzle-orm'
import { z } from 'zod'
import { nanoid } from 'nanoid'
import { requireAuth } from '~~/server/utils/session'

const bodySchema = z.object({
  date: z.string().regex(/^\d{4}-\d{2}-\d{2}$/), // YYYY-MM-DD format
  completed: z.boolean(),
  notes: z.string().optional(),
  stressLevel: z.number().optional(), // 0-1
  emotion: z.string().optional(),
})

interface AnalyzeResponse {
  stress_score: number
  emotion: {
    emotion: string
  }
}

export default defineEventHandler(async (event) => {
  const user = await requireAuth(event)
  const body = await readValidatedBody(event, bodySchema.parse)
  const config = useRuntimeConfig()

  // Auto-analyze notes if present
  let stressLevel = body.stressLevel
  let emotion = body.emotion

  if (body.notes && body.notes.trim().length > 0) {
    try {
      const analysis = await $fetch<AnalyzeResponse>(`${config.fastApiUrl}/recommend/analyze`, {
        method: 'POST',
        body: { text: body.notes },
      })

      // Only set if not explicitly provided
      if (stressLevel === undefined) stressLevel = analysis.stress_score
      if (emotion === undefined) emotion = analysis.emotion.emotion
    } catch (e) {
      console.error('Failed to analyze notes:', e)
      // Continue without analysis
    }
  }

  // Check if entry already exists for this date
  const existing = await db
    .select({ id: dailyHabitLogs.id })
    .from(dailyHabitLogs)
    .where(and(eq(dailyHabitLogs.userId, user.id), eq(dailyHabitLogs.date, body.date)))

    .limit(1)

  if (existing.length > 0) {
    // Update existing entry
    const [updated] = await db
      .update(dailyHabitLogs)
      .set({
        completed: body.completed,
        notes: body.notes,
        ...(stressLevel !== undefined ? { stressLevel } : {}),
        ...(emotion !== undefined ? { emotion } : {}),
      })
      .where(eq(dailyHabitLogs.id, existing[0].id))
      .returning()

    return { log: updated, action: 'updated' }
  }

  // Create new entry
  const [created] = await db
    .insert(dailyHabitLogs)
    .values({
      id: nanoid(),
      userId: user.id,
      date: body.date,
      completed: body.completed,
      notes: body.notes,
      stressLevel,
      emotion,
    })
    .returning()

  return { log: created, action: 'created' }
})
