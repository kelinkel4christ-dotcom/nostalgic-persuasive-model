import { db } from '~~/server/utils/db'
import { requireAdmin } from '~~/server/utils/admin'
import { user, userPreferences, dailyHabitLogs } from '~~/server/database/schema'
import { eq } from 'drizzle-orm'

export default defineEventHandler(async (event) => {
  requireAdmin(event)

  // Fetch all habit logs with user preferences
  const data = await db
    .select({
      logId: dailyHabitLogs.id,
      date: dailyHabitLogs.date,
      completed: dailyHabitLogs.completed,
      notes: dailyHabitLogs.notes,
      stressLevel: dailyHabitLogs.stressLevel,
      emotion: dailyHabitLogs.emotion,
      createdAt: dailyHabitLogs.createdAt,
      userId: dailyHabitLogs.userId,
      userName: user.name,
      userEmail: user.email,
      experimentGroup: userPreferences.experimentGroup,
      habitType: userPreferences.habitType,
      birthYear: userPreferences.birthYear,
    })
    .from(dailyHabitLogs)
    .innerJoin(user, eq(dailyHabitLogs.userId, user.id))
    .leftJoin(userPreferences, eq(dailyHabitLogs.userId, userPreferences.userId))
    .orderBy(dailyHabitLogs.date)

  // Generate CSV
  const headers = [
    'Log ID',
    'Date',
    'Completed',
    'Stress Level',
    'Emotion',
    'Notes',
    'User ID',
    'User Name',
    'User Email',
    'Experiment Group',
    'Habit Type',
    'Birth Year',
    'Created At',
  ]

  const csvRows = [headers.join(',')]

  for (const row of data) {
    const values = [
      row.logId,
      row.date,
      row.completed ? 'Yes' : 'No',
      row.stressLevel?.toFixed(3) ?? '',
      row.emotion ?? '',
      `"${(row.notes ?? '').replace(/"/g, '""')}"`,
      row.userId,
      `"${row.userName}"`,
      row.userEmail,
      row.experimentGroup ?? '',
      row.habitType ?? '',
      row.birthYear?.toString() ?? '',
      row.createdAt.toISOString(),
    ]
    csvRows.push(values.join(','))
  }

  const csv = csvRows.join('\n')

  // Set headers for CSV download
  setHeader(event, 'Content-Type', 'text/csv')
  setHeader(
    event,
    'Content-Disposition',
    `attachment; filename="habit-logs-export-${new Date().toISOString().split('T')[0]}.csv"`
  )

  return csv
})
