import { db } from '~~/server/utils/db'
import { requireAdmin } from '~~/server/utils/admin'
import { userPreferences, contentFeedback } from '~~/server/database/schema'
import { eq } from 'drizzle-orm'

export default defineEventHandler(async (event) => {
  requireAdmin(event)

  // Fetch all interaction logs with user group info
  const data = await db
    .select({
      interactionId: contentFeedback.id,
      timestamp: contentFeedback.createdAt,
      userId: contentFeedback.userId,
      interactionType: contentFeedback.interactionType,
      contentType: contentFeedback.contentType,
      contentId: contentFeedback.contentId,
      duration: contentFeedback.durationSeconds,
      feedback: contentFeedback.bringsBackMemories,
      experimentGroup: userPreferences.experimentGroup,
    })
    .from(contentFeedback)
    // We join preferences to get the A/B group assignment
    .leftJoin(userPreferences, eq(contentFeedback.userId, userPreferences.userId))
    .orderBy(contentFeedback.createdAt)

  // Generate CSV
  const headers = [
    'Log ID',
    'Timestamp',
    'User ID',
    'Group',
    'Interaction Type',
    'Content Type',
    'Content ID',
    'Duration (s)',
    'Explicit Feedback (Memories)',
  ]

  const csvRows = [headers.join(',')]

  for (const row of data) {
    const values = [
      row.interactionId,
      row.timestamp.toISOString(),
      row.userId,
      row.experimentGroup ?? 'unknown',
      row.interactionType,
      row.contentType,
      row.contentId,
      row.duration?.toString() ?? '0',
      row.feedback === null ? 'N/A' : row.feedback ? 'Yes' : 'No',
    ]
    csvRows.push(values.join(','))
  }

  const csv = csvRows.join('\n')

  // Set headers for CSV download
  setHeader(event, 'Content-Type', 'text/csv')
  setHeader(
    event,
    'Content-Disposition',
    `attachment; filename="interaction-logs-export-${new Date().toISOString().split('T')[0]}.csv"`
  )

  return csv
})
