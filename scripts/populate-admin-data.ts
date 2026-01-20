import { db } from '../server/utils/db'
import { user, account } from '../server/database/schema/auth-schema'
import { userPreferences } from '../server/database/schema/user-preferences-schema'
import { dailyHabitLogs, contentFeedback } from '../server/database/schema/habit-log-schema'
import { songs, movies } from '../server/database/schema/content-schema'
import { nanoid } from 'nanoid'
import { eq } from 'drizzle-orm'
import crypto from 'crypto'

const TARGET_EMAIL = 'email@email.com'
const DAYS_OF_HABIT_LOGS = 30
const DAYS_OF_CONTENT_FEEDBACK = 7

const TREATMENT_EMAILS = [
  'user1@test.com',
  'user2@test.com',
  'user3@test.com',
  'user4@test.com',
  'user5@test.com',
]

const CONTROL_EMAILS = [
  'user6@test.com',
  'user7@test.com',
  'user8@test.com',
  'user9@test.com',
  'user10@test.com',
]

async function hashPassword(password: string): Promise<string> {
  const encoder = new TextEncoder()
  const data = encoder.encode(password)
  const hash = await crypto.subtle.digest('SHA-256', data)
  return Buffer.from(hash).toString('hex')
}

async function getRandomContentIds() {
  const songIds = await db.select({ id: songs.id }).from(songs).limit(100)
  const movieIds = await db.select({ id: movies.id }).from(movies).limit(100)
  return {
    songIds: songIds.map((s) => s.id),
    movieIds: movieIds.map((m) => String(m.id)),
  }
}

async function createUserIfNotExists(
  email: string,
  _group: 'treatment' | 'control'
): Promise<string> {
  const existing = await db.select().from(user).where(eq(user.email, email)).limit(1)

  if (existing.length > 0) {
    console.log(`  ✓ User exists: ${email}`)
    return existing[0].id
  }

  const userId = nanoid()
  const passwordHash = await hashPassword('password123')

  await db.insert(user).values({
    id: userId,
    name: email.split('@')[0].replace(/\d/g, '').replace(/user/, 'User '),
    email,
    emailVerified: false,
  })

  await db.insert(account).values({
    id: nanoid(),
    accountId: userId,
    providerId: 'email',
    userId,
    password: passwordHash,
    createdAt: new Date(),
    updatedAt: new Date(),
  })

  console.log(`  + Created: ${email}`)
  return userId
}

async function createUserPreferencesIfNotExists(userId: string, group: 'treatment' | 'control') {
  const existing = await db
    .select()
    .from(userPreferences)
    .where(eq(userPreferences.userId, userId))
    .limit(1)

  if (existing.length > 0) {
    return
  }

  await db.insert(userPreferences).values({
    id: nanoid(),
    userId,
    habitType: Math.random() > 0.5 ? 'exercise' : 'smoking_cessation',
    experimentGroup: group,
    nostalgicPeriodStart: 1990 + Math.floor(Math.random() * 15),
    nostalgicPeriodEnd: 2005 + Math.floor(Math.random() * 10),
    researchConsent: true,
    selectedMovieIds: [],
    selectedSongIds: [],
    onboardingCompletedAt: new Date(Date.now() - Math.random() * 30 * 24 * 60 * 60 * 1000),
  })
}

function generateHabitLogs(
  userId: string,
  group: 'treatment' | 'control',
  _content: { songIds: string[]; movieIds: string[] }
) {
  const logs = []
  const today = new Date()

  const positiveNotes = [
    'Felt great after completing my habit today!',
    'Energy is through the roof!',
    'So glad I pushed through.',
    'Making progress feels amazing.',
    'Consistency is key!',
    'Crushing it today!',
  ]
  const neutralNotes = [
    'Just a regular day.',
    'Did what I needed to do.',
    'Average day, but still showed up.',
    'Completed the habit on autopilot.',
  ]
  const negativeNotes = [
    'Struggled a bit today, but still managed.',
    'Not my best day, but I tried.',
    'Low motivation, barely got it done.',
    'Harder than usual, but I persisted.',
  ]
  const missNotes = [
    'Too busy with work today.',
    'Didnt have time in the morning.',
    'Completely forgot.',
    'Feeling under the weather.',
    'Life got in the way.',
  ]

  for (let i = 0; i < DAYS_OF_HABIT_LOGS; i++) {
    const date = new Date(today)
    date.setDate(date.getDate() - i)
    const dateStr = date.toISOString().split('T')[0]
    const dayOfWeek = date.getDay()
    const isWeekend = dayOfWeek === 0 || dayOfWeek === 6

    const baseCompletionRate = group === 'treatment' ? 0.78 : 0.65
    const adjustedRate = isWeekend ? baseCompletionRate - 0.1 : baseCompletionRate
    const completed = Math.random() < adjustedRate

    let baseStress = 0.5 - (i / DAYS_OF_HABIT_LOGS) * 0.25
    if (!completed) {
      baseStress += 0.15 + Math.random() * 0.15
    }
    const stressLevel = Math.min(0.9, Math.max(0.1, baseStress + (Math.random() - 0.5) * 0.15))

    let emotion: string
    if (stressLevel > 0.7) emotion = Math.random() > 0.5 ? 'fear' : 'anger'
    else if (stressLevel > 0.5) emotion = Math.random() > 0.6 ? 'sadness' : 'neutral'
    else if (stressLevel > 0.35) emotion = Math.random() > 0.5 ? 'neutral' : 'surprise'
    else emotion = Math.random() > 0.4 ? 'joy' : 'love'

    let notes: string
    if (completed) {
      if (stressLevel > 0.6) notes = negativeNotes[Math.floor(Math.random() * negativeNotes.length)]
      else if (stressLevel > 0.4)
        notes = neutralNotes[Math.floor(Math.random() * neutralNotes.length)]
      else notes = positiveNotes[Math.floor(Math.random() * positiveNotes.length)]
    } else {
      notes = missNotes[Math.floor(Math.random() * missNotes.length)]
    }

    logs.push({
      id: nanoid(),
      userId,
      date: dateStr,
      completed,
      notes,
      stressLevel: parseFloat(stressLevel.toFixed(2)),
      emotion,
      createdAt: new Date(),
      updatedAt: new Date(),
    })
  }

  return logs
}

function generateContentFeedback(
  userId: string,
  group: 'treatment' | 'control',
  content: { songIds: string[]; movieIds: string[] }
) {
  const feedbacks = []
  const today = new Date()

  const numInteractions =
    group === 'treatment' ? 10 + Math.floor(Math.random() * 6) : 7 + Math.floor(Math.random() * 5)

  for (let i = 0; i < numInteractions; i++) {
    const date = new Date(today)
    date.setDate(date.getDate() - Math.floor(Math.random() * DAYS_OF_CONTENT_FEEDBACK))
    date.setHours(Math.floor(Math.random() * 12) + 8, Math.floor(Math.random() * 60))

    const isSong = Math.random() > 0.5
    const contentId = isSong
      ? content.songIds[Math.floor(Math.random() * content.songIds.length)]
      : content.movieIds[Math.floor(Math.random() * content.movieIds.length)]

    let interactionType: 'view' | 'click' | 'skip' | 'next' | 'replay' | 'feedback'
    const rand = Math.random()
    if (rand < 0.35) interactionType = 'view'
    else if (rand < 0.55) interactionType = 'click'
    else if (rand < 0.7) interactionType = 'next'
    else if (rand < 0.82) interactionType = 'skip'
    else if (rand < 0.92) interactionType = 'replay'
    else interactionType = 'feedback'

    let durationSeconds: number | null = null
    let bringsBackMemories: boolean | null = null

    switch (interactionType) {
      case 'view':
        durationSeconds = 3 + Math.floor(Math.random() * 5)
        break
      case 'click':
        durationSeconds = 8 + Math.floor(Math.random() * 10)
        break
      case 'next':
        durationSeconds = 2 + Math.floor(Math.random() * 4)
        break
      case 'skip':
        durationSeconds = 1 + Math.floor(Math.random() * 3)
        break
      case 'replay':
        durationSeconds = 15 + Math.floor(Math.random() * 20)
        break
      case 'feedback':
        durationSeconds = 5 + Math.floor(Math.random() * 8)
        bringsBackMemories = group === 'treatment' ? Math.random() < 0.72 : Math.random() < 0.48
        break
    }

    feedbacks.push({
      id: nanoid(),
      userId,
      contentType: isSong ? 'song' : 'movie',
      contentId,
      interactionType,
      durationSeconds,
      bringsBackMemories,
      createdAt: date,
    })
  }

  return feedbacks
}

async function main() {
  console.log('🌱 Starting comprehensive data population for admin page...\n')

  // Get random content IDs
  console.log('📚 Fetching random content IDs...')
  const content = await getRandomContentIds()
  console.log(`  Found ${content.songIds.length} songs, ${content.movieIds.length} movies\n`)

  // Step 1: Handle target user
  console.log('👤 Step 1: Verifying target user...')
  const targetExisting = await db.select().from(user).where(eq(user.email, TARGET_EMAIL)).limit(1)
  let targetUserId: string
  if (targetExisting.length > 0) {
    targetUserId = targetExisting[0].id
    console.log(`  ✓ Target user exists: ${TARGET_EMAIL}\n`)
  } else {
    console.log('  ! Target user not found, skipping...\n')
    targetUserId = ''
  }

  // Step 2: Create treatment users
  console.log('👥 Step 2: Creating treatment users...')
  const treatmentUserIds: string[] = []
  for (const email of TREATMENT_EMAILS) {
    const userId = await createUserIfNotExists(email, 'treatment')
    treatmentUserIds.push(userId)
    await createUserPreferencesIfNotExists(userId, 'treatment')
  }
  if (targetUserId) treatmentUserIds.unshift(targetUserId)
  console.log(`  Total treatment users: ${treatmentUserIds.length}\n`)

  // Step 3: Create control users
  console.log('👥 Step 3: Creating control users...')
  const controlUserIds: string[] = []
  for (const email of CONTROL_EMAILS) {
    const userId = await createUserIfNotExists(email, 'control')
    controlUserIds.push(userId)
    await createUserPreferencesIfNotExists(userId, 'control')
  }
  console.log(`  Total control users: ${controlUserIds.length}\n`)

  // Step 4: Generate habit logs
  console.log('📝 Step 4: Generating habit logs...')
  const allUserIds = [...treatmentUserIds, ...controlUserIds]

  let habitLogsInserted = 0
  let habitLogsSkipped = 0

  for (const userId of allUserIds) {
    const group = treatmentUserIds.includes(userId) ? 'treatment' : 'control'
    const logs = generateHabitLogs(userId, group, content)

    for (const log of logs) {
      try {
        await db.insert(dailyHabitLogs).values(log).onConflictDoNothing()
        habitLogsInserted++
      } catch {
        habitLogsSkipped++
      }
    }
  }
  console.log(`  ✓ Inserted ${habitLogsInserted} habit logs (${habitLogsSkipped} skipped)\n`)

  // Step 5: Generate content feedback
  console.log('💬 Step 5: Generating content feedback...')

  let feedbackInserted = 0
  let feedbackSkipped = 0

  for (const userId of allUserIds) {
    const group = treatmentUserIds.includes(userId) ? 'treatment' : 'control'
    const feedbacks = generateContentFeedback(userId, group, content)

    for (const feedback of feedbacks) {
      try {
        await db.insert(contentFeedback).values(feedback).onConflictDoNothing()
        feedbackInserted++
      } catch {
        feedbackSkipped++
      }
    }
  }
  console.log(`  ✓ Inserted ${feedbackInserted} feedback entries (${feedbackSkipped} skipped)\n`)

  // Summary
  console.log('📊 Summary:')
  console.log(
    `  Users: ${allUserIds.length} total (${treatmentUserIds.length} treatment, ${controlUserIds.length} control)`
  )
  console.log(`  Habit Logs: ${habitLogsInserted} inserted`)
  console.log(`  Content Feedback: ${feedbackInserted} inserted`)

  console.log('\n✨ Admin page is ready for screenshots!')
  process.exit(0)
}

main().catch((err) => {
  console.error('❌ Error:', err)
  process.exit(1)
})
