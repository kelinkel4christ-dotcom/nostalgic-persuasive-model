import { relations } from 'drizzle-orm'
import {
  pgTable,
  text,
  boolean,
  timestamp,
  date,
  index,
  unique,
  pgEnum,
  real,
  integer,
} from 'drizzle-orm/pg-core'
import { user } from './auth-schema'

// Content feedback type enum
export const contentTypeEnum = pgEnum('content_type', ['song', 'movie'])
export const interactionTypeEnum = pgEnum('interaction_type', [
  'view',
  'click',
  'skip',
  'next',
  'replay',
  'feedback',
])

// Daily habit logs - tracks whether user completed their habit each day
export const dailyHabitLogs = pgTable(
  'daily_habit_logs',
  {
    id: text('id').primaryKey(),
    userId: text('user_id')
      .notNull()
      .references(() => user.id, { onDelete: 'cascade' }),
    date: date('date').notNull(),
    completed: boolean('completed').notNull(),
    notes: text('notes'),
    stressLevel: real('stress_level'), // 0-1 score from stress model
    emotion: text('emotion'), // Predicted emotion (e.g., 'Happy', 'Sad')
    createdAt: timestamp('created_at').defaultNow().notNull(),
    updatedAt: timestamp('updated_at')
      .defaultNow()
      .$onUpdate(() => new Date())
      .notNull(),
  },
  (table) => [
    index('daily_habit_logs_user_id_idx').on(table.userId),
    index('daily_habit_logs_date_idx').on(table.date),
    unique('daily_habit_logs_user_date_unique').on(table.userId, table.date),
  ]
)

// Content feedback - stores "brings back memories" responses and interaction logs
export const contentFeedback = pgTable(
  'content_feedback',
  {
    id: text('id').primaryKey(),
    userId: text('user_id')
      .notNull()
      .references(() => user.id, { onDelete: 'cascade' }),
    contentType: contentTypeEnum('content_type').notNull(),
    contentId: text('content_id').notNull(), // song ID or movie ID
    interactionType: interactionTypeEnum('interaction_type').notNull().default('feedback'),
    durationSeconds: integer('duration_seconds'), // How long they engaged
    bringsBackMemories: boolean('brings_back_memories'), // Nullable for non-feedback events
    createdAt: timestamp('created_at').defaultNow().notNull(),
  },
  (table) => [
    index('content_feedback_user_id_idx').on(table.userId),
    index('content_feedback_content_idx').on(table.contentType, table.contentId),
  ]
)

// Relations
export const dailyHabitLogsRelations = relations(dailyHabitLogs, ({ one }) => ({
  user: one(user, {
    fields: [dailyHabitLogs.userId],
    references: [user.id],
  }),
}))

export const contentFeedbackRelations = relations(contentFeedback, ({ one }) => ({
  user: one(user, {
    fields: [contentFeedback.userId],
    references: [user.id],
  }),
}))
