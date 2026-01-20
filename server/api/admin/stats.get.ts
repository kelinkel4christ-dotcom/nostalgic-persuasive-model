import { db } from '~~/server/utils/db'
import { requireAdmin } from '~~/server/utils/admin'
import { user, userPreferences, dailyHabitLogs, contentFeedback } from '~~/server/database/schema'
import { sql, count, avg, eq } from 'drizzle-orm'

export default defineEventHandler(async (event) => {
  requireAdmin(event)

  // 1. Get user counts by group
  const groupCounts = await db
    .select({
      experimentGroup: userPreferences.experimentGroup,
      count: count(),
    })
    .from(userPreferences)
    .groupBy(userPreferences.experimentGroup)

  // 2. Get total users
  const [totalUsers] = await db.select({ count: count() }).from(user)
  const userCount = totalUsers?.count ?? 0

  // 3. Get total habit logs
  const [totalLogs] = await db.select({ count: count() }).from(dailyHabitLogs)

  // 4. Get average stress by group
  const stressByGroup = await db
    .select({
      experimentGroup: userPreferences.experimentGroup,
      avgStress: avg(dailyHabitLogs.stressLevel),
      logCount: count(),
    })
    .from(dailyHabitLogs)
    .innerJoin(userPreferences, eq(dailyHabitLogs.userId, userPreferences.userId))
    .groupBy(userPreferences.experimentGroup)

  // 5. Get habit completion rate by group
  const completionByGroup = await db
    .select({
      experimentGroup: userPreferences.experimentGroup,
      totalLogs: count(),
      completedLogs: sql<number>`sum(case when ${dailyHabitLogs.completed} then 1 else 0 end)`,
    })
    .from(dailyHabitLogs)
    .innerJoin(userPreferences, eq(dailyHabitLogs.userId, userPreferences.userId))
    .groupBy(userPreferences.experimentGroup)

  // 6. Get content feedback stats (treatment only - explicit feedback)
  const [feedbackStats] = await db
    .select({
      totalFeedback: count(),
      positiveFeedback: sql<number>`sum(case when ${contentFeedback.bringsBackMemories} then 1 else 0 end)`,
    })
    .from(contentFeedback)
    .where(eq(contentFeedback.interactionType, 'feedback'))

  // 7. Get Detailed Interaction Stats by Group (For the new dashboard)
  const rawInteractions = await db
    .select({
      experimentGroup: userPreferences.experimentGroup,
      interactionType: contentFeedback.interactionType,
      count: count(),
      duration: sql<number>`sum(${contentFeedback.durationSeconds})`,
      positiveCount: sql<number>`sum(case when ${contentFeedback.bringsBackMemories} then 1 else 0 end)`,
    })
    .from(contentFeedback)
    .leftJoin(userPreferences, eq(contentFeedback.userId, userPreferences.userId))
    .groupBy(userPreferences.experimentGroup, contentFeedback.interactionType)

  // 8. Get Active User Count (Users with at least one log or interaction)
  // We use a raw query for the UNION of active users
  const activeUsersResult = await db.execute(sql`
    SELECT COUNT(DISTINCT user_id) as count
    FROM (
      SELECT user_id FROM ${dailyHabitLogs}
      UNION
      SELECT user_id FROM ${contentFeedback}
    ) as active_users
  `)
  const activeUserCount = Number(activeUsersResult[0]?.count ?? 0)

  // --- Processing Data ---

  // Helper to extract group counts
  const getGroupCount = (group: string) =>
    groupCounts.find((g) => g.experimentGroup === group)?.count ?? 0
  const treatmentCount = getGroupCount('treatment')
  const controlCount = getGroupCount('control')

  // Helper to process interactions
  const processGroupInteractions = (group: string, userCount: number) => {
    const groupRows = rawInteractions.filter((r) => r.experimentGroup === group)
    const views = groupRows.find((r) => r.interactionType === 'view')?.count ?? 0
    const clicks = groupRows.find((r) => r.interactionType === 'click')?.count ?? 0
    const skips = groupRows.find((r) => r.interactionType === 'skip')?.count ?? 0
    const replays = groupRows.find((r) => r.interactionType === 'replay')?.count ?? 0
    const nexts = groupRows.find((r) => r.interactionType === 'next')?.count ?? 0
    const feedback = groupRows.find((r) => r.interactionType === 'feedback')?.count ?? 0

    const totalInteractions = views + clicks + skips + replays + nexts + feedback
    const totalDuration = groupRows.reduce((sum, r) => sum + Number(r.duration || 0), 0)

    // Regret = Skips / Views (Standard Rejection Rate)
    // Views = Total impressions. Skips = Rejected impressions.
    const regretRate = views > 0 ? (skips / views) * 100 : 0

    // CTR = Clicks / Views
    const ctr = views > 0 ? (clicks / views) * 100 : 0

    // Positive Response Rate = Positive / Total Feedback
    const feedbackRow = groupRows.find((r) => r.interactionType === 'feedback')
    const feedbackCount = feedbackRow?.count ?? 0
    const positiveFeedback = Number(feedbackRow?.positiveCount ?? 0)
    const positiveResponseRate = feedbackCount > 0 ? (positiveFeedback / feedbackCount) * 100 : 0

    // Per-User Normalization
    // We avoid division by zero if a group has no users yet
    const safeUserCount = userCount > 0 ? userCount : 1
    const viewsPerUser = views / safeUserCount
    const interactionsPerUser = totalInteractions / safeUserCount
    const durationPerUser = totalDuration / safeUserCount
    // Quality Metric: Avg duration per view (How long do they stick around per card?)
    const durationPerView = views > 0 ? totalDuration / views : 0

    return {
      views,
      clicks,
      skips,
      nexts,
      replays,
      feedback,
      totalInteractions,
      totalDuration,
      regretRate,
      ctr,
      positiveResponseRate,
      // Normalized Metrics
      viewsPerUser,
      interactionsPerUser,
      durationPerUser,
      durationPerView,
    }
  }

  const treatmentInteractions = processGroupInteractions('treatment', treatmentCount)
  const controlInteractions = processGroupInteractions('control', controlCount)

  // Global Engagement Metrics
  const globalDuration = treatmentInteractions.totalDuration + controlInteractions.totalDuration
  const globalInteractions =
    treatmentInteractions.totalInteractions + controlInteractions.totalInteractions

  // Regret Score (Global)
  const globalSkips = treatmentInteractions.skips + controlInteractions.skips
  const globalViews = treatmentInteractions.views + controlInteractions.views
  const globalRegret = globalViews > 0 ? (globalSkips / globalViews) * 100 : 0

  // Existing stats helpers
  const treatmentStress = stressByGroup.find((g) => g.experimentGroup === 'treatment')
  const controlStress = stressByGroup.find((g) => g.experimentGroup === 'control')
  const treatmentCompletion = completionByGroup.find((g) => g.experimentGroup === 'treatment')
  const controlCompletion = completionByGroup.find((g) => g.experimentGroup === 'control')

  // Use activeUserCount for global averages if available, otherwise fallback to total
  const denominator = activeUserCount > 0 ? activeUserCount : userCount

  return {
    overview: {
      totalUsers: userCount,
      activeUsers: activeUserCount,
      treatmentUsers: treatmentCount,
      controlUsers: controlCount,
      totalHabitLogs: totalLogs?.count ?? 0,
    },
    // NEW: Global Engagement
    engagement: {
      avgTimeOnPlatform: denominator > 0 ? globalDuration / denominator : 0, // seconds
      regretRate: globalRegret,
      avgInteractions: denominator > 0 ? globalInteractions / denominator : 0,
    },
    // NEW: Group Behavior
    groupBehavior: {
      treatment: treatmentInteractions,
      control: controlInteractions,
    },
    stressComparison: {
      treatment: {
        avgStress: treatmentStress?.avgStress ? Number(treatmentStress.avgStress) : null,
        logCount: treatmentStress?.logCount ?? 0,
      },
      control: {
        avgStress: controlStress?.avgStress ? Number(controlStress.avgStress) : null,
        logCount: controlStress?.logCount ?? 0,
      },
    },
    completionComparison: {
      treatment: {
        total: treatmentCompletion?.totalLogs ?? 0,
        completed: treatmentCompletion?.completedLogs ?? 0,
        rate:
          treatmentCompletion?.totalLogs && treatmentCompletion.totalLogs > 0
            ? (Number(treatmentCompletion.completedLogs) / treatmentCompletion.totalLogs) * 100
            : 0,
      },
      control: {
        total: controlCompletion?.totalLogs ?? 0,
        completed: controlCompletion?.completedLogs ?? 0,
        rate:
          controlCompletion?.totalLogs && controlCompletion.totalLogs > 0
            ? (Number(controlCompletion.completedLogs) / controlCompletion.totalLogs) * 100
            : 0,
      },
    },
    nostalgiaFeedback: {
      total: feedbackStats?.totalFeedback ?? 0,
      positive: feedbackStats?.positiveFeedback ?? 0,
      positiveRate:
        feedbackStats?.totalFeedback && feedbackStats.totalFeedback > 0
          ? (Number(feedbackStats.positiveFeedback) / feedbackStats.totalFeedback) * 100
          : 0,
    },
  }
})
