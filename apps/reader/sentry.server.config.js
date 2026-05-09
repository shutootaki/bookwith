// This file configures the initialization of Sentry on the server.
// The config you add here will be used whenever the server handles a request.
// https://docs.sentry.io/platforms/javascript/guides/nextjs/

import * as Sentry from '@sentry/nextjs'

// H-19: 上流フォークの DSN を fallback で指していたため削除。
const SENTRY_DSN = process.env.SENTRY_DSN || process.env.NEXT_PUBLIC_SENTRY_DSN

const TRACES_SAMPLE_RATE = (() => {
  const raw =
    process.env.SENTRY_TRACES_SAMPLE_RATE ||
    process.env.NEXT_PUBLIC_SENTRY_TRACES_SAMPLE_RATE
  const parsed = raw ? Number.parseFloat(raw) : NaN
  if (!Number.isFinite(parsed) || parsed < 0 || parsed > 1) {
    return process.env.NODE_ENV === 'production' ? 0.1 : 1.0
  }
  return parsed
})()

if (SENTRY_DSN) {
  Sentry.init({
    dsn: SENTRY_DSN,
    tracesSampleRate: TRACES_SAMPLE_RATE,
  })
}
