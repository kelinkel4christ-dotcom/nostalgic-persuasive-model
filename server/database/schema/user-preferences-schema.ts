import { relations } from 'drizzle-orm'
import {
  pgTable,
  text,
  integer,
  boolean,
  timestamp,
  jsonb,
  pgEnum,
  index,
} from 'drizzle-orm/pg-core'
import { user } from './auth-schema'

export const habitTypeEnum = pgEnum('habit_type', ['exercise', 'smoking_cessation'])
export const experimentGroupEnum = pgEnum('experiment_group', ['treatment', 'control'])

export const userPreferences = pgTable(
  'user_preferences',
  {
    id: text('id').primaryKey(),
    userId: text('user_id')
      .notNull()
      .references(() => user.id, { onDelete: 'cascade' })
      .unique(),
    birthYear: integer('birth_year'),
    experimentGroup: experimentGroupEnum('experiment_group').notNull().default('treatment'),
    habitType: habitTypeEnum('habit_type').notNull(),
    nostalgicPeriodStart: integer('nostalgic_period_start'),
    nostalgicPeriodEnd: integer('nostalgic_period_end'),
    selectedMovieIds: jsonb('selected_movie_ids').$type<number[]>().default([]),
    selectedSongIds: jsonb('selected_song_ids').$type<string[]>().default([]),
    researchConsent: boolean('research_consent').default(false).notNull(),
    onboardingCompletedAt: timestamp('onboarding_completed_at'),
    tutorialCompletedAt: timestamp('tutorial_completed_at'),
    tutorialSkippedAt: timestamp('tutorial_skipped_at'),
    createdAt: timestamp('created_at').defaultNow().notNull(),
    updatedAt: timestamp('updated_at')
      .defaultNow()
      .$onUpdate(() => new Date())
      .notNull(),
  },
  (table) => [index('user_preferences_user_id_idx').on(table.userId)]
)

export const userPreferencesRelations = relations(userPreferences, ({ one }) => ({
  user: one(user, {
    fields: [userPreferences.userId],
    references: [user.id],
  }),
}))
