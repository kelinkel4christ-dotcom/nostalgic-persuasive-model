import { db } from '~~/server/utils/db'
import { songs } from '~~/server/database/schema'
import { sql, ilike, and, gte, lte, notInArray, inArray, desc } from 'drizzle-orm'
import { z } from 'zod'

const querySchema = z.object({
  yearStart: z.coerce.number().optional(),
  yearEnd: z.coerce.number().optional(),
  search: z.string().optional(),
  limit: z.coerce.number().min(1).max(50).default(20),
  excludeIds: z.string().optional(), // comma-separated IDs
  mode: z.enum(['random', 'popular', 'similar']).optional().default('random'),
  selectedIds: z.string().optional(), // comma-separated IDs for similar mode
})

export default defineEventHandler(async (event) => {
  const query = await getValidatedQuery(event, querySchema.parse)

  // Enforce 10-year age gap (Nostalgia Rule)
  const currentYear = new Date().getFullYear()
  const maxAllowedYear = currentYear - 10

  // Cap yearEnd at maxAllowedYear
  const effectiveYearEnd = query.yearEnd ? Math.min(query.yearEnd, maxAllowedYear) : maxAllowedYear

  const conditions = []

  // Year filtering
  if (query.yearStart) {
    conditions.push(gte(songs.year, query.yearStart))
  }
  // Use effectiveYearEnd instead of query.yearEnd
  conditions.push(lte(songs.year, effectiveYearEnd))

  // Search filtering (by name or artist)
  if (query.search && query.search.trim()) {
    const searchTerm = `%${query.search.trim()}%`
    conditions.push(
      sql`(${ilike(songs.name, searchTerm)} OR ${songs.artists}::text ILIKE ${searchTerm})`
    )
  }

  // Exclude already selected IDs
  if (query.excludeIds) {
    const excludeList = query.excludeIds.split(',').filter(Boolean)
    if (excludeList.length > 0) {
      conditions.push(notInArray(songs.id, excludeList))
    }
  }

  // Mode: similar - use FastAPI recommender
  if (query.mode === 'similar' && query.selectedIds) {
    const selectedList = query.selectedIds.split(',').filter(Boolean)

    if (selectedList.length > 0) {
      try {
        const config = useRuntimeConfig()
        const fastApiUrl = config.fastApiUrl || 'http://localhost:8000'

        const response = await $fetch<{
          recommendations: Array<{
            spotify_id: string
            name: string
            artists: string
            genre: string
            year: number
            similarity: number
          }>
        }>(`${fastApiUrl}/songs/recommend`, {
          method: 'POST',
          body: {
            liked_song_ids: selectedList,
            n_recommendations: query.limit,
          },
        })

        // Get full song details from database
        const songIds = response.recommendations.map((r) => r.spotify_id)
        const excludeList = query.excludeIds ? query.excludeIds.split(',').filter(Boolean) : []

        const results = await db
          .select({
            id: songs.id,
            name: songs.name,
            albumName: songs.albumName,
            artists: songs.artists,
            year: songs.year,
            genre: songs.genre,
          })
          .from(songs)
          .where(
            and(
              inArray(songs.id, songIds),
              excludeList.length > 0 ? notInArray(songs.id, excludeList) : undefined
            )
          )
          .limit(query.limit)

        return {
          items: results,
          count: results.length,
          mode: 'similar',
        }
      } catch (error) {
        // Fall back to popular if FastAPI fails
        console.error('FastAPI song recommend error:', error)
      }
    }
  }

  // Mode: popular - order by popularity descending
  if (query.mode === 'popular') {
    const results = await db
      .select({
        id: songs.id,
        name: songs.name,
        albumName: songs.albumName,
        artists: songs.artists,
        year: songs.year,
        genre: songs.genre,
      })
      .from(songs)
      .where(conditions.length > 0 ? and(...conditions) : undefined)
      .orderBy(desc(songs.popularity))
      .limit(query.limit)

    return {
      items: results,
      count: results.length,
      mode: 'popular',
    }
  }

  // Search Mode: Order by popularity
  // CRITICAL FIX: Ignore yearStart for search to allow finding older classics
  // even if they are outside the specific user era. Still enforce maxAllowedYear.
  if (query.search && query.search.trim()) {
    const searchTerm = `%${query.search.trim()}%`
    const searchConditions = [
      lte(songs.year, effectiveYearEnd),
      sql`(${ilike(songs.name, searchTerm)} OR ${songs.artists}::text ILIKE ${searchTerm})`,
    ]

    if (query.excludeIds) {
      const excludeList = query.excludeIds.split(',').filter(Boolean)
      if (excludeList.length > 0) {
        searchConditions.push(notInArray(songs.id, excludeList))
      }
    }

    const results = await db
      .select({
        id: songs.id,
        name: songs.name,
        albumName: songs.albumName,
        artists: songs.artists,
        year: songs.year,
        genre: songs.genre,
      })
      .from(songs)
      .where(and(...searchConditions))
      .orderBy(desc(songs.popularity))
      .limit(query.limit)

    return {
      items: results,
      count: results.length,
      mode: 'search',
    }
  }

  // Default: random sampling for variety
  const results = await db
    .select({
      id: songs.id,
      name: songs.name,
      albumName: songs.albumName,
      artists: songs.artists,
      year: songs.year,
      genre: songs.genre,
    })
    .from(songs)
    .where(conditions.length > 0 ? and(...conditions) : undefined)
    .orderBy(sql`RANDOM()`)
    .limit(query.limit)

  return {
    items: results,
    count: results.length,
    mode: 'random',
  }
})
