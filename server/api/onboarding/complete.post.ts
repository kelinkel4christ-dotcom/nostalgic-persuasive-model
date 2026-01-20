import { db } from '~~/server/utils/db'
import { userPreferences } from '~~/server/database/schema'
import { requireAuth } from '~~/server/utils/session'
import { z } from 'zod'
import { nanoid } from 'nanoid'

// Schema supports both treatment (full onboarding) and control (minimal onboarding)
const bodySchema = z.discriminatedUnion('experimentGroup', [
  // Treatment group: full data required
  z.object({
    experimentGroup: z.literal('treatment'),
    birthYear: z.number().min(1920).max(2020),
    habitType: z.enum(['exercise', 'smoking_cessation']),
    nostalgicPeriodStart: z.number().optional(),
    nostalgicPeriodEnd: z.number().optional(),
    selectedMovieIds: z.array(z.number()).min(5).max(5),
    selectedSongIds: z.array(z.string()).min(5).max(5),
    researchConsent: z.boolean(),
  }),
  // Control group: minimal data (no birth year, no favorites)
  z.object({
    experimentGroup: z.literal('control'),
    habitType: z.enum(['exercise', 'smoking_cessation']),
    researchConsent: z.boolean(),
  }),
])

export default defineEventHandler(async (event) => {
  const user = await requireAuth(event)
  const body = await readValidatedBody(event, bodySchema.parse)

  // Build values based on group
  const values = {
    id: nanoid(),
    userId: user.id,
    experimentGroup: body.experimentGroup,
    habitType: body.habitType,
    researchConsent: body.researchConsent,
    onboardingCompletedAt: new Date(),
    // Only set these for treatment group
    birthYear: body.experimentGroup === 'treatment' ? body.birthYear : null,
    nostalgicPeriodStart:
      body.experimentGroup === 'treatment' ? (body.nostalgicPeriodStart ?? null) : null,
    nostalgicPeriodEnd:
      body.experimentGroup === 'treatment' ? (body.nostalgicPeriodEnd ?? null) : null,
    selectedMovieIds: body.experimentGroup === 'treatment' ? body.selectedMovieIds : [],
    selectedSongIds: body.experimentGroup === 'treatment' ? body.selectedSongIds : [],
  }

  // Upsert user preferences
  await db
    .insert(userPreferences)
    .values(values)
    .onConflictDoUpdate({
      target: userPreferences.userId,
      set: {
        experimentGroup: body.experimentGroup,
        habitType: body.habitType,
        researchConsent: body.researchConsent,
        onboardingCompletedAt: new Date(),
        birthYear: values.birthYear,
        nostalgicPeriodStart: values.nostalgicPeriodStart,
        nostalgicPeriodEnd: values.nostalgicPeriodEnd,
        selectedMovieIds: values.selectedMovieIds,
        selectedSongIds: values.selectedSongIds,
      },
    })

  return {
    success: true,
    message: 'Onboarding completed successfully',
  }
})
