import { drizzle } from 'drizzle-orm/postgres-js'
import * as schema from '../database/schema'
import * as path from 'path'
import type { Logger } from 'drizzle-orm/logger'
import winston from 'winston'
import DailyRotateFile from 'winston-daily-rotate-file'

// Configure Winston logger with rotation
const rotateTransport = new DailyRotateFile({
  filename: path.resolve(process.cwd(), 'logs', 'drizzle-%DATE%.log'),
  datePattern: 'YYYY-MM-DD-HH',
  zippedArchive: true,
  maxSize: '20m',
  maxFiles: '1d', // Keep logs for 1 day (24 hours) with hourly rotation
  format: winston.format.combine(
    winston.format.timestamp(),
    winston.format.printf(({ timestamp, message }) => {
      return `[${timestamp}] ${message}`
    })
  ),
})

const logger = winston.createLogger({
  transports: [rotateTransport],
})

class WinstonLogger implements Logger {
  logQuery(query: string, params: unknown[]): void {
    const logEntry = `Query: ${query} ${params.length ? `| Params: ${JSON.stringify(params)}` : ''}`
    logger.info(logEntry)
  }
}

export const db = drizzle(process.env.DATABASE_URL!, {
  schema,
  logger: new WinstonLogger(),
  casing: 'snake_case',
})
