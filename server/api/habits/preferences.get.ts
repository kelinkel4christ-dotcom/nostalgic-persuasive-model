import { db } from '~~/server/utils/db'
import { userPreferences } from '~~/server/database/schema'
import { eq } from 'drizzle-orm'
import { requireAuth } from '~~/server/utils/session'

export default defineEventHandler(async (event) => {
  const user = await requireAuth(event)

  const [prefs] = await db
    .select({
      birthYear: userPreferences.birthYear,
      habitType: userPreferences.habitType,
      experimentGroup: userPreferences.experimentGroup,
      researchConsent: userPreferences.researchConsent,
      onboardingCompletedAt: userPreferences.onboardingCompletedAt,
      nostalgicPeriodStart: userPreferences.nostalgicPeriodStart,
      nostalgicPeriodEnd: userPreferences.nostalgicPeriodEnd,
    })
    .from(userPreferences)
    .where(eq(userPreferences.userId, user.id))
    .limit(1)

  if (!prefs) {
    return { preferences: null, onboardingComplete: false }
  }

  // Use stored nostalgic period or calculate from birth year if not set
  const nostalgicPeriodStart =
    prefs.nostalgicPeriodStart ?? (prefs.birthYear ? prefs.birthYear + 5 : null)
  const nostalgicPeriodEnd =
    prefs.nostalgicPeriodEnd ??
    (prefs.birthYear ? Math.min(prefs.birthYear + 19, new Date().getFullYear() - 1) : null)

  return {
    preferences: {
      ...prefs,
      nostalgicPeriodStart,
      nostalgicPeriodEnd,
    },
    onboardingComplete: !!prefs.onboardingCompletedAt,
  }
})
