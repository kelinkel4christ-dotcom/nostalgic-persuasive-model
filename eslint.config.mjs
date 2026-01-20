import withNuxt from './.nuxt/eslint.config.mjs'

export default withNuxt(
  {
    ignores: [
      'fastapi-backend/**',
      'training/**',
      'models/**',
      'dataset/**',
      'writeup/**',
      '**/*.py',
    ],
  },
  {
    rules: {
      'no-console': 'off',
    },
  }
)
