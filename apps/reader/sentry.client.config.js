// This file configures the initialization of Sentry on the browser.
// The config you add here will be used whenever a page is visited.
// https://docs.sentry.io/platforms/javascript/guides/nextjs/

import * as Sentry from '@sentry/nextjs'

// H-19: ハードコードされた fallback DSN は他組織の Sentry プロジェクトを指していたため削除。
// `SENTRY_DSN` / `NEXT_PUBLIC_SENTRY_DSN` 未設定の場合は Sentry を初期化しない。
const SENTRY_DSN = process.env.SENTRY_DSN || process.env.NEXT_PUBLIC_SENTRY_DSN

// `tracesSampleRate` を環境変数で制御し、本番で 1.0 のままコスト増になる事故を防ぐ。
// 開発時は 1.0、本番は 0.1〜0.2 程度を推奨。
const TRACES_SAMPLE_RATE = (() => {
  const raw =
    process.env.SENTRY_TRACES_SAMPLE_RATE ||
    process.env.NEXT_PUBLIC_SENTRY_TRACES_SAMPLE_RATE
  const parsed = raw ? Number.parseFloat(raw) : NaN
  if (!Number.isFinite(parsed) || parsed < 0 || parsed > 1) {
    // デフォルトは保守的（dev: 1.0 / prod: 0.1）
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
