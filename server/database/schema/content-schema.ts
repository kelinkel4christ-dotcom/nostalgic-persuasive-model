import { pgTable, text, integer, real, jsonb, timestamp, index } from 'drizzle-orm/pg-core'

// Songs table - from Spotify 550K dataset
export const songs = pgTable(
  'songs',
  {
    id: text('id').primaryKey(), // Spotify track ID
    name: text('name').notNull(),
    albumName: text('album_name'),
    artists: jsonb('artists').$type<string[]>(), // Array of artist names
    danceability: real('danceability'),
    energy: real('energy'),
    key: integer('key'),
    loudness: real('loudness'),
    mode: integer('mode'),
    speechiness: real('speechiness'),
    acousticness: real('acousticness'),
    instrumentalness: real('instrumentalness'),
    liveness: real('liveness'),
    valence: real('valence'),
    tempo: real('tempo'),
    durationMs: integer('duration_ms'),
    lyrics: text('lyrics'),
    year: integer('year'),
    genre: text('genre'),
    popularity: integer('popularity'),
    nicheGenres: jsonb('niche_genres').$type<string[]>(),
    createdAt: timestamp('created_at').defaultNow().notNull(),
  },
  (table) => [
    index('songs_year_idx').on(table.year),
    index('songs_genre_idx').on(table.genre),
    index('songs_popularity_idx').on(table.popularity),
  ]
)

// Movies table - 100K records from MovieLens ml-32m dataset
export const movies = pgTable(
  'movies',
  {
    id: integer('id').primaryKey(), // MovieLens movie ID
    title: text('title').notNull(), // Title without year
    year: integer('year'), // Extracted from original title
    genres: jsonb('genres').$type<string[]>(), // Array of genres
    ratingCount: integer('rating_count'), // Number of ratings
    avgRating: real('avg_rating'), // Average rating (0-5)
    createdAt: timestamp('created_at').defaultNow().notNull(),
  },
  (table) => [
    index('movies_year_idx').on(table.year),
    index('movies_rating_count_idx').on(table.ratingCount),
  ]
)
