import { db } from '~~/server/utils/db'
import { dailyHabitLogs } from '~~/server/database/schema'
import { eq, and, gte, lte } from 'drizzle-orm'
import { z } from 'zod'
import { requireAuth } from '~~/server/utils/session'

const querySchema = z.object({
  month: z
    .string()
    .regex(/^\d{4}-\d{2}$/)
    .optional(), // YYYY-MM format
  startDate: z
    .string()
    .regex(/^\d{4}-\d{2}-\d{2}$/)
    .optional(),
  endDate: z
    .string()
    .regex(/^\d{4}-\d{2}-\d{2}$/)
    .optional(),
})

export default defineEventHandler(async (event) => {
  const user = await requireAuth(event)
  const query = await getValidatedQuery(event, querySchema.parse)

  let startDate: string
  let endDate: string

  if (query.month) {
    // Parse month to get start and end dates
    const [year, month] = query.month.split('-').map(Number)
    startDate = `${year}-${String(month).padStart(2, '0')}-01`
    const lastDay = new Date(year, month, 0).getDate()
    endDate = `${year}-${String(month).padStart(2, '0')}-${lastDay}`
  } else if (query.startDate && query.endDate) {
    startDate = query.startDate
    endDate = query.endDate
  } else {
    // Default to current month
    const now = new Date()
    const year = now.getFullYear()
    const month = now.getMonth() + 1
    startDate = `${year}-${String(month).padStart(2, '0')}-01`
    const lastDay = new Date(year, month, 0).getDate()
    endDate = `${year}-${String(month).padStart(2, '0')}-${lastDay}`
  }

  const logs = await db
    .select({
      id: dailyHabitLogs.id,
      date: dailyHabitLogs.date,
      completed: dailyHabitLogs.completed,
      notes: dailyHabitLogs.notes,
      stressLevel: dailyHabitLogs.stressLevel,
      emotion: dailyHabitLogs.emotion,
    })
    .from(dailyHabitLogs)
    .where(
      and(
        eq(dailyHabitLogs.userId, user.id),
        gte(dailyHabitLogs.date, startDate),
        lte(dailyHabitLogs.date, endDate)
      )
    )

  return {
    logs,
    period: { startDate, endDate },
  }
})
