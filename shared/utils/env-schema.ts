import { z } from 'zod'

export const envSchema = z.object({
  BETTER_AUTH_SECRET: z.string().min(32),
  BETTER_AUTH_URL: z.url(),
  DATABASE_URL: z.url(),
  FASTAPI_URL: z.url(),
})

export type Env = z.infer<typeof envSchema>
