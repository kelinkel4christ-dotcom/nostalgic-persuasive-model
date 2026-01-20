import { z } from 'zod'
import { envSchema } from '~~/shared/utils/env-schema'

export default defineNitroPlugin(() => {
  const result = envSchema.safeParse(process.env)

  if (!result.success) {
    const prettyError = z.prettifyError(result.error)

    if (import.meta.dev) {
      console.error('❌ Invalid environment variables:')
      console.error(prettyError)
      return
    }

    throw createError({
      statusCode: 500,
      statusMessage: 'Invalid environment variables',
      message: prettyError,
    })
  }

  console.log('✅ Environment variables validated')
})
