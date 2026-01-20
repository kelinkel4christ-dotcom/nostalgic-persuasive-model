import { db } from '../server/utils/db'
import { user } from '../server/database/schema/auth-schema'
import { dailyHabitLogs } from '../server/database/schema/habit-log-schema'
import { nanoid } from 'nanoid'

async function main() {
  console.log('🌱 Starting history population...')

  // 1. Get the first user
  const users = await db.select().from(user).limit(1)

  if (users.length === 0) {
    console.error('❌ No users found! Please register a user first.')
    process.exit(1)
  }

  const targetUser = users[0]
  console.log(`👤 Populating data for user: ${targetUser.name} (${targetUser.email})`)

  // 2. Generate 14 days of data
  const logsToInsert = []
  // const emotions = ['joy', 'sadness', 'anger', 'fear', 'love', 'surprise', 'neutral']
  const notes = [
    'Had a great workout today!',
    'Feeling a bit tired but pushed through.',
    'Stressed about work, missed the habit.',
    'Really happy with my progress.',
    'Just a normal day.',
    'Anxious about the upcoming deadline.',
    'Relaxed and feeling good.',
  ]

  for (let i = 0; i < 14; i++) {
    const date = new Date()
    date.setDate(date.getDate() - i)
    const dateStr = date.toISOString().split('T')[0]

    // Randomize data
    // Create a trend: stress decreases over time (higher i = further back = higher stress)
    const baseStress = 0.3 + Math.random() * 0.2 // 0.3 - 0.5 base
    const stressTrend = (i / 14) * 0.4 // Add up to 0.4 for older entries
    const stressLevel = Math.min(0.95, Math.max(0.1, baseStress + stressTrend))

    // Random emotion based on stress (kind of)
    let emotion = 'neutral'
    if (stressLevel > 0.7) emotion = Math.random() > 0.5 ? 'fear' : 'anger'
    else if (stressLevel > 0.4) emotion = Math.random() > 0.5 ? 'sadness' : 'neutral'
    else emotion = Math.random() > 0.3 ? 'joy' : 'love'

    logsToInsert.push({
      id: nanoid(),
      userId: targetUser.id,
      date: dateStr,
      completed: Math.random() > 0.3, // 70% completion rate
      notes: notes[Math.floor(Math.random() * notes.length)],
      stressLevel: parseFloat(stressLevel.toFixed(2)),
      emotion: emotion,
      createdAt: new Date(),
      updatedAt: new Date(),
    })
  }

  // 3. Insert into DB
  try {
    console.log(`📝 Inserting ${logsToInsert.length} log entries...`)

    // Insert one by one to avoid conflicts (skip if exists)
    for (const log of logsToInsert) {
      await db.insert(dailyHabitLogs).values(log).onConflictDoNothing() // Skip if date already logged
    }

    console.log('✅ History populated successfully!')
  } catch (error) {
    console.error('❌ Failed to populate history:', error)
  }

  process.exit(0)
}

main()
