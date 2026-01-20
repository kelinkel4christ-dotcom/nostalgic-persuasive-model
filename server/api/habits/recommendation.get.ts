import { z } from 'zod'
import { requireAuth } from '~~/server/utils/session'

// Types matching FastAPI response
type RecommendedContent = {
  type: 'song' | 'movie'
  id: string
  title?: string
  genres?: string[]
  name?: string
  artists?: string[]
  genre?: string
  year?: number
}

type EmotionResult = {
  emotion: string
  confidence: number
  probabilities: Record<string, number>
}

type RecommendResponse = {
  content: RecommendedContent
  stress_score: number
  emotion: EmotionResult
  bandit_score: number
}

// Query params for optional journal text
const querySchema = z.object({
  journalText: z.string().optional().default(''),
})

export default defineEventHandler(async (event) => {
  const user = await requireAuth(event)
  const query = await getValidatedQuery(event, querySchema.parse)

  // Get FastAPI URL from runtime config
  const config = useRuntimeConfig()
  const fastApiUrl = config.fastApiUrl || 'http://localhost:8000'

  try {
    // Call FastAPI unified recommend endpoint
    const response = await $fetch<RecommendResponse>(`${fastApiUrl}/recommend`, {
      method: 'POST',
      body: {
        user_id: user.id,
        journal_text: query.journalText,
      },
    })

    // Transform to frontend format
    const content = response.content

    if (content.type === 'song') {
      return {
        type: 'song' as const,
        content: {
          id: content.id,
          name: content.name || 'Unknown',
          albumName: null,
          artists: content.artists || null,
          year: content.year || null,
          genre: content.genre || null,
        },
        analysis: {
          stressScore: response.stress_score,
          emotion: response.emotion,
          banditScore: response.bandit_score,
        },
      }
    }

    return {
      type: 'movie' as const,
      content: {
        id: parseInt(content.id, 10),
        title: content.title || 'Unknown',
        year: content.year || null,
        genres: content.genres || null,
      },
      analysis: {
        stressScore: response.stress_score,
        emotion: response.emotion,
        banditScore: response.bandit_score,
      },
    }
  } catch (error) {
    console.error('FastAPI recommend error:', error)

    // Fallback to error
    throw createError({
      statusCode: 503,
      message: 'Recommendation service temporarily unavailable',
    })
  }
})
