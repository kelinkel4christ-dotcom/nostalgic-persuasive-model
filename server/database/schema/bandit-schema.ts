import { pgTable, text, integer, timestamp } from 'drizzle-orm/pg-core'

// Bandit models table - stores serialized bandit models (global and per-user)
// Using text with base64 encoding for portability (bytea handling varies by driver)
export const banditModels = pgTable('bandit_models', {
  modelId: text('model_id').primaryKey(), // 'global' or 'user_{user_id}'
  modelData: text('model_data').notNull(), // Base64 encoded serialized model
  nUpdates: integer('n_updates').default(0),
  updatedAt: timestamp('updated_at').defaultNow().notNull(),
})
