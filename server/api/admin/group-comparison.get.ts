import { db } from '~~/server/utils/db'
import { requireAdmin } from '~~/server/utils/admin'
import { userPreferences, dailyHabitLogs } from '~~/server/database/schema'
import { sql, count, eq } from 'drizzle-orm'

export default defineEventHandler(async (event) => {
  requireAdmin(event)

  // Emotion distribution by group
  const emotionsByGroup = await db
    .select({
      experimentGroup: userPreferences.experimentGroup,
      emotion: dailyHabitLogs.emotion,
      count: count(),
    })
    .from(dailyHabitLogs)
    .innerJoin(userPreferences, eq(dailyHabitLogs.userId, userPreferences.userId))
    .where(sql`${dailyHabitLogs.emotion} IS NOT NULL`)
    .groupBy(userPreferences.experimentGroup, dailyHabitLogs.emotion)

  // Stress level distribution by group (buckets: low 0-0.33, medium 0.33-0.66, high 0.66-1)
  const stressDistribution = await db
    .select({
      experimentGroup: userPreferences.experimentGroup,
      lowStress: sql<number>`sum(case when ${dailyHabitLogs.stressLevel} < 0.33 then 1 else 0 end)`,
      mediumStress: sql<number>`sum(case when ${dailyHabitLogs.stressLevel} >= 0.33 and ${dailyHabitLogs.stressLevel} < 0.66 then 1 else 0 end)`,
      highStress: sql<number>`sum(case when ${dailyHabitLogs.stressLevel} >= 0.66 then 1 else 0 end)`,
      total: count(),
    })
    .from(dailyHabitLogs)
    .innerJoin(userPreferences, eq(dailyHabitLogs.userId, userPreferences.userId))
    .where(sql`${dailyHabitLogs.stressLevel} IS NOT NULL`)
    .groupBy(userPreferences.experimentGroup)

  // Format emotion data
  const treatmentEmotions: Record<string, number> = {}
  const controlEmotions: Record<string, number> = {}

  for (const row of emotionsByGroup) {
    if (!row.emotion) continue
    if (row.experimentGroup === 'treatment') {
      treatmentEmotions[row.emotion] = row.count
    } else {
      controlEmotions[row.emotion] = row.count
    }
  }

  // Format stress data
  const treatmentStress = stressDistribution.find((r) => r.experimentGroup === 'treatment')
  const controlStress = stressDistribution.find((r) => r.experimentGroup === 'control')

  return {
    emotions: {
      treatment: treatmentEmotions,
      control: controlEmotions,
    },
    stressDistribution: {
      treatment: {
        low: Number(treatmentStress?.lowStress ?? 0),
        medium: Number(treatmentStress?.mediumStress ?? 0),
        high: Number(treatmentStress?.highStress ?? 0),
      },
      control: {
        low: Number(controlStress?.lowStress ?? 0),
        medium: Number(controlStress?.mediumStress ?? 0),
        high: Number(controlStress?.highStress ?? 0),
      },
    },
  }
})
