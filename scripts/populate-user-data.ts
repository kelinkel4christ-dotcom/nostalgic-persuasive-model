import { db } from '../server/utils/db'
import { user, account } from '../server/database/schema/auth-schema'
import { userPreferences } from '../server/database/schema/user-preferences-schema'
import { dailyHabitLogs } from '../server/database/schema/habit-log-schema'
import { nanoid } from 'nanoid'
import { eq } from 'drizzle-orm'
import crypto from 'crypto'

const TARGET_EMAIL = 'email@email.com'
const TARGET_PASSWORD = 'password'
const DAYS_OF_DATA = 30

async function hashPassword(password: string): Promise<string> {
  const encoder = new TextEncoder()
  const data = encoder.encode(password)
  const hash = await crypto.subtle.digest('SHA-256', data)
  return Buffer.from(hash).toString('hex')
}

async function main() {
  console.log('🌱 Starting user data population...\n')

  // Step 1: Check if user exists
  const existingUsers = await db.select().from(user).where(eq(user.email, TARGET_EMAIL)).limit(1)

  let targetUserId: string

  if (existingUsers.length > 0) {
    targetUserId = existingUsers[0].id
    console.log(`✅ User already exists: ${TARGET_EMAIL} (ID: ${targetUserId})`)
  } else {
    // Create user
    targetUserId = nanoid()
    const passwordHash = await hashPassword(TARGET_PASSWORD)

    await db.insert(user).values({
      id: targetUserId,
      name: 'Test User',
      email: TARGET_EMAIL,
      emailVerified: false,
    })

    await db.insert(account).values({
      id: nanoid(),
      accountId: targetUserId,
      providerId: 'email',
      userId: targetUserId,
      password: passwordHash,
      createdAt: new Date(),
      updatedAt: new Date(),
    })

    console.log(`✅ Created new user: ${TARGET_EMAIL} (ID: ${targetUserId})`)
  }

  // Step 2: Create user preferences if not exists
  const existingPrefs = await db
    .select()
    .from(userPreferences)
    .where(eq(userPreferences.userId, targetUserId))
    .limit(1)

  if (existingPrefs.length === 0) {
    await db.insert(userPreferences).values({
      id: nanoid(),
      userId: targetUserId,
      habitType: 'exercise',
      experimentGroup: 'treatment',
      nostalgicPeriodStart: 1990,
      nostalgicPeriodEnd: 2010,
      researchConsent: true,
      selectedMovieIds: [],
      selectedSongIds: [],
      onboardingCompletedAt: new Date(),
    })
    console.log('✅ Created user preferences')
  } else {
    console.log('✅ User preferences already exist')
  }

  // Step 3: Generate 30 days of realistic habit logs
  console.log(`\n📝 Generating ${DAYS_OF_DATA} days of realistic habit data...`)

  const positiveNotes = [
    'Felt great after completing my habit today!',
    'Energy is through the roof!',
    'Best morning routine ever.',
    'So glad I pushed through.',
    'Making progress feels amazing.',
    'Consistency is key!',
    'Crushing it today!',
    'Feeling strong and motivated.',
  ]
  const neutralNotes = [
    'Just a regular day.',
    'Did what I needed to do.',
    'Average day, but still showed up.',
    'Completed the habit on autopilot.',
    'Steady progress as usual.',
    'Nothing special, but done is done.',
  ]
  const negativeNotes = [
    'Struggled a bit today, but still managed.',
    'Not my best day, but I tried.',
    'Low motivation, barely got it done.',
    'Harder than usual, but I persisted.',
    'Feeling tired but proud I completed it.',
    'Almost skipped, glad I didnt.',
  ]
  const missNotes = [
    'Too busy with work today.',
    'Didnt have time in the morning.',
    'Completely forgot.',
    'Feeling under the weather.',
    'Life got in the way.',
    'Missed it, will do better tomorrow.',
    'Completely overwhelmed today.',
  ]

  const logsToInsert = []
  const today = new Date()

  for (let i = 0; i < DAYS_OF_DATA; i++) {
    const date = new Date(today)
    date.setDate(date.getDate() - i)
    const dateStr = date.toISOString().split('T')[0]
    const dayOfWeek = date.getDay()

    // Realistic patterns
    // Weekend: slightly lower completion rate (0.6 instead of 0.75)
    const isWeekend = dayOfWeek === 0 || dayOfWeek === 6
    const baseCompletionRate = isWeekend ? 0.6 : 0.78

    // Streak logic: higher chance of completion if previous days were completed
    // This creates realistic streak patterns
    const completed = Math.random() < baseCompletionRate

    // Stress level: varies based on completion and time
    // Recent days have lower stress (improving trend)
    // Non-completion increases stress
    let baseStress = 0.5 - (i / DAYS_OF_DATA) * 0.3 // Stress decreases over time
    if (!completed) {
      baseStress += 0.15 + Math.random() * 0.2
    }
    const stressLevel = Math.min(0.95, Math.max(0.1, baseStress + (Math.random() - 0.5) * 0.2))

    // Emotion based on stress level
    let emotion: string
    if (stressLevel > 0.75) {
      emotion = Math.random() > 0.5 ? 'fear' : 'anger'
    } else if (stressLevel > 0.5) {
      emotion = Math.random() > 0.6 ? 'sadness' : Math.random() > 0.5 ? 'fear' : 'neutral'
    } else if (stressLevel > 0.35) {
      emotion = Math.random() > 0.5 ? 'neutral' : 'surprise'
    } else {
      emotion = Math.random() > 0.4 ? 'joy' : 'love'
    }

    // Notes based on completion and stress
    let notes: string
    if (completed) {
      if (stressLevel > 0.6) {
        notes = negativeNotes[Math.floor(Math.random() * negativeNotes.length)]
      } else if (stressLevel > 0.4) {
        notes = neutralNotes[Math.floor(Math.random() * neutralNotes.length)]
      } else {
        notes = positiveNotes[Math.floor(Math.random() * positiveNotes.length)]
      }
    } else {
      notes = missNotes[Math.floor(Math.random() * missNotes.length)]
    }

    logsToInsert.push({
      id: nanoid(),
      userId: targetUserId,
      date: dateStr,
      completed,
      notes,
      stressLevel: parseFloat(stressLevel.toFixed(2)),
      emotion,
      createdAt: new Date(),
      updatedAt: new Date(),
    })
  }

  // Insert logs
  let inserted = 0
  let skipped = 0
  for (const log of logsToInsert) {
    try {
      await db.insert(dailyHabitLogs).values(log).onConflictDoNothing()
      inserted++
    } catch {
      skipped++
    }
  }

  console.log(`✅ Inserted ${inserted} habit log entries (${skipped} already existed)`)

  // Summary
  const completedCount = logsToInsert.filter((l) => l.completed).length
  const avgStress = logsToInsert.reduce((sum, l) => sum + l.stressLevel, 0) / logsToInsert.length
  console.log(`\n📊 Summary:`)
  console.log(`   - Total days: ${DAYS_OF_DATA}`)
  console.log(
    `   - Completed: ${completedCount} (${Math.round((completedCount / DAYS_OF_DATA) * 100)}%)`
  )
  console.log(`   - Avg stress: ${avgStress.toFixed(2)}`)

  console.log('\n✨ Done! User is ready for screenshots.')
  process.exit(0)
}

main().catch((err) => {
  console.error('❌ Error:', err)
  process.exit(1)
})
