import { parse } from 'csv-parse'
import { createReadStream } from 'fs'
import { db } from '../utils/db'
import { songs, movies } from './schema'
import { sql, eq } from 'drizzle-orm'
import path from 'path'

const BATCH_SIZE = 1000

// ============================================================================
// CLI Arguments Parser
// ============================================================================

type SeedTarget = 'all' | 'songs' | 'movies' | 'ratings'

function parseArgs(): { target: SeedTarget; clearFirst: boolean } {
  const args = process.argv.slice(2)
  let target: SeedTarget = 'all'
  let clearFirst = true

  for (const arg of args) {
    if (arg === '--songs' || arg === '-s') {
      target = 'songs'
    } else if (arg === '--movies' || arg === '-m') {
      target = 'movies'
    } else if (arg === '--ratings' || arg === '-r') {
      target = 'ratings'
    } else if (arg === '--no-clear' || arg === '-n') {
      clearFirst = false
    } else if (arg === '--help' || arg === '-h') {
      printHelp()
      process.exit(0)
    }
  }

  return { target, clearFirst }
}

function printHelp(): void {
  console.log(`
🌱 Database Seed Script

Usage: bun run db:seed [options]

Options:
  --songs, -s      Seed only songs
  --movies, -m     Seed only movies (with ratings)
  --ratings, -r    Update only movie ratings (no re-insert)
  --no-clear, -n   Skip clearing existing data before insert
  --help, -h       Show this help message

Examples:
  bun run db:seed                 # Full seed (clear all, seed all)
  bun run db:seed --songs         # Seed only songs
  bun run db:seed --movies        # Seed only movies with ratings
  bun run db:seed --ratings       # Update ratings for existing movies
  bun run db:seed --songs -n      # Add songs without clearing existing
`)
}

// ============================================================================
// Data Types
// ============================================================================

interface SongRow {
  id: string
  name: string
  album_name: string
  artists: string
  danceability: string
  energy: string
  key: string
  loudness: string
  mode: string
  speechiness: string
  acousticness: string
  instrumentalness: string
  liveness: string
  valence: string
  tempo: string
  duration_ms: string
  lyrics: string
  year: string
  genre: string
  popularity: string
  total_artist_followers: string
  avg_artist_popularity: string
  artist_ids: string
  niche_genres: string
}

interface MovieRow {
  movieId: string
  title: string
  genres: string
}

interface RatingStats {
  count: number
  sum: number
}

// ============================================================================
// Utilities
// ============================================================================

function parseJsonArray(value: string): string[] {
  if (!value || value === '[]') return []
  try {
    return JSON.parse(value.replace(/'/g, '"'))
  } catch {
    return []
  }
}

function extractYearFromTitle(title: string): { cleanTitle: string; year: number | null } {
  const match = title.match(/\((\d{4})\)\s*$/)
  if (match) {
    return {
      cleanTitle: title.replace(/\s*\(\d{4}\)\s*$/, '').trim(),
      year: parseInt(match[1], 10),
    }
  }
  return { cleanTitle: title, year: null }
}

// ============================================================================
// Rating Stats Loader
// ============================================================================

async function loadRatingStats(): Promise<Map<number, RatingStats>> {
  console.log('📊 Loading rating statistics from ratings.csv...')

  const ratingsPath = path.resolve(process.cwd(), 'dataset/ml-32m/ratings.csv')
  const stats = new Map<number, RatingStats>()

  const parser = createReadStream(ratingsPath).pipe(
    parse({
      columns: true,
      skip_empty_lines: true,
    })
  )

  let processed = 0
  for await (const row of parser as AsyncIterable<{ movieId: string; rating: string }>) {
    const movieId = parseInt(row.movieId, 10)
    const rating = parseFloat(row.rating)

    const existing = stats.get(movieId)
    if (existing) {
      existing.count++
      existing.sum += rating
    } else {
      stats.set(movieId, { count: 1, sum: rating })
    }

    processed++
    if (processed % 5_000_000 === 0) {
      console.log(`  Processed ${processed / 1_000_000}M ratings...`)
    }
  }

  console.log(`  Loaded stats for ${stats.size} movies from ${processed} ratings`)
  return stats
}

// ============================================================================
// Seed Functions
// ============================================================================

async function seedSongs() {
  console.log('🎵 Seeding songs...')

  const songsPath = path.resolve(
    process.cwd(),
    'dataset/550k Spotify Songs Audio, Lyrics & Genres/songs.csv'
  )

  let batch: (typeof songs.$inferInsert)[] = []
  let count = 0
  let skipped = 0

  const parser = createReadStream(songsPath).pipe(
    parse({
      columns: true,
      skip_empty_lines: true,
      relax_quotes: true,
      relax_column_count: true,
    })
  )

  for await (const row of parser as AsyncIterable<SongRow>) {
    if (!row.id || !row.name) {
      skipped++
      continue
    }

    batch.push({
      id: row.id,
      name: row.name,
      albumName: row.album_name || null,
      artists: parseJsonArray(row.artists),
      danceability: row.danceability ? parseFloat(row.danceability) : null,
      energy: row.energy ? parseFloat(row.energy) : null,
      key: row.key ? parseInt(row.key, 10) : null,
      loudness: row.loudness ? parseFloat(row.loudness) : null,
      mode: row.mode ? parseInt(row.mode, 10) : null,
      speechiness: row.speechiness ? parseFloat(row.speechiness) : null,
      acousticness: row.acousticness ? parseFloat(row.acousticness) : null,
      instrumentalness: row.instrumentalness ? parseFloat(row.instrumentalness) : null,
      liveness: row.liveness ? parseFloat(row.liveness) : null,
      valence: row.valence ? parseFloat(row.valence) : null,
      tempo: row.tempo ? parseFloat(row.tempo) : null,
      durationMs: row.duration_ms ? parseInt(row.duration_ms, 10) : null,
      lyrics: null,
      year: row.year ? parseInt(row.year, 10) : null,
      genre: row.genre || null,
      popularity: row.popularity ? parseInt(row.popularity, 10) : null,
      nicheGenres: parseJsonArray(row.niche_genres),
    })

    if (batch.length >= BATCH_SIZE) {
      await db.insert(songs).values(batch).onConflictDoNothing()
      count += batch.length
      console.log(`  Inserted ${count} songs...`)
      batch = []
    }
  }

  if (batch.length > 0) {
    await db.insert(songs).values(batch).onConflictDoNothing()
    count += batch.length
  }

  console.log(`✅ Seeded ${count} songs (skipped ${skipped} invalid rows)`)
}

async function seedMovies(ratingStats: Map<number, RatingStats>) {
  console.log('🎬 Seeding movies...')

  const moviesPath = path.resolve(process.cwd(), 'dataset/ml-32m/movies.csv')

  let batch: (typeof movies.$inferInsert)[] = []
  let count = 0
  let withRatings = 0

  const parser = createReadStream(moviesPath).pipe(
    parse({
      columns: true,
      skip_empty_lines: true,
    })
  )

  for await (const row of parser as AsyncIterable<MovieRow>) {
    const { cleanTitle, year } = extractYearFromTitle(row.title)
    const movieId = parseInt(row.movieId, 10)

    const stats = ratingStats.get(movieId)
    const ratingCount = stats?.count ?? null
    const avgRating = stats ? stats.sum / stats.count : null

    if (ratingCount) withRatings++

    batch.push({
      id: movieId,
      title: cleanTitle,
      year,
      genres: row.genres ? row.genres.split('|') : [],
      ratingCount,
      avgRating,
    })

    if (batch.length >= BATCH_SIZE) {
      await db.insert(movies).values(batch).onConflictDoNothing()
      count += batch.length
      console.log(`  Inserted ${count} movies...`)
      batch = []
    }
  }

  if (batch.length > 0) {
    await db.insert(movies).values(batch).onConflictDoNothing()
    count += batch.length
  }

  console.log(`✅ Seeded ${count} movies (${withRatings} with rating data)`)
}

async function updateRatingsOnly(ratingStats: Map<number, RatingStats>) {
  console.log('📈 Updating movie ratings only...')

  let updated = 0
  let processed = 0

  for (const [movieId, stats] of ratingStats) {
    const avgRating = stats.sum / stats.count

    const result = await db
      .update(movies)
      .set({
        ratingCount: stats.count,
        avgRating: avgRating,
      })
      .where(eq(movies.id, movieId))
      .returning({ id: movies.id })

    if (result.length > 0) {
      updated++
    }

    processed++
    if (processed % 10000 === 0) {
      console.log(`  Processed ${processed} movies (${updated} updated)...`)
    }
  }

  console.log(`✅ Updated ratings for ${updated} movies`)
}

// ============================================================================
// Main Entry Point
// ============================================================================

async function main() {
  const { target, clearFirst } = parseArgs()

  console.log('🌱 Starting database seed...')
  console.log(`   Target: ${target}`)
  console.log(`   Clear first: ${clearFirst}`)
  console.log('')

  // Handle ratings-only update (no clearing)
  if (target === 'ratings') {
    const ratingStats = await loadRatingStats()
    console.log('')
    await updateRatingsOnly(ratingStats)
    console.log('')
    console.log('🎉 Rating update complete!')
    process.exit(0)
  }

  // Clear data if requested
  if (clearFirst) {
    console.log('🗑️  Clearing existing content data...')
    if (target === 'all' || target === 'songs') {
      await db.delete(songs)
      console.log('   Cleared songs')
    }
    if (target === 'all' || target === 'movies') {
      await db.delete(movies)
      console.log('   Cleared movies')
    }
    console.log('')
  }

  // Load rating stats if needed
  let ratingStats: Map<number, RatingStats> | null = null
  if (target === 'all' || target === 'movies') {
    ratingStats = await loadRatingStats()
    console.log('')
  }

  // Seed based on target
  if (target === 'all' || target === 'songs') {
    await seedSongs()
    console.log('')
  }

  if (target === 'all' || target === 'movies') {
    await seedMovies(ratingStats!)
    console.log('')
  }

  console.log('🎉 Database seeding complete!')

  // Print counts
  if (target === 'all' || target === 'songs') {
    const [songCount] = await db.select({ count: sql<number>`count(*)` }).from(songs)
    console.log(`   📊 Total songs: ${songCount.count}`)
  }
  if (target === 'all' || target === 'movies') {
    const [movieCount] = await db.select({ count: sql<number>`count(*)` }).from(movies)
    console.log(`   📊 Total movies: ${movieCount.count}`)
  }

  process.exit(0)
}

main().catch((err) => {
  console.error('❌ Seeding failed:', err)
  process.exit(1)
})
