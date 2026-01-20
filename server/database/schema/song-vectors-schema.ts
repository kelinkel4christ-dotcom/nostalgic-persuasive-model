import { index, pgTable, serial, text, timestamp, vector } from 'drizzle-orm/pg-core'
import { songs } from './content-schema'

// Song vectors table for content-based similarity search
// Uses pgvector for efficient cosine similarity queries
export const songVectors = pgTable(
  'song_vectors',
  {
    id: serial('id').primaryKey(),
    spotifyId: text('spotify_id')
      .notNull()
      .unique()
      .references(() => songs.id, { onDelete: 'cascade' }),
    embedding: vector('embedding', { dimensions: 128 }).notNull(),
    createdAt: timestamp('created_at').defaultNow().notNull(),
    updatedAt: timestamp('updated_at').defaultNow().notNull(),
  },
  (table) => [
    index('song_vectors_embedding_idx').using('hnsw', table.embedding.op('vector_cosine_ops')),
    index('song_vectors_spotify_id_idx').on(table.spotifyId),
  ]
)

// Type exports
export type SongVector = typeof songVectors.$inferSelect
export type NewSongVector = typeof songVectors.$inferInsert
