import type { auth } from '../utils/auth'

export type User = typeof auth.$Infer.Session.user

declare module 'h3' {
  interface H3EventContext {
    user?: User
  }
}
