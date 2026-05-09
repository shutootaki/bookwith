// next.config.mjs
import path from 'path'
import { fileURLToPath } from 'url' // Needed to replicate __dirname

// Import functions for wrappers
import nextBundleAnalyzer from '@next/bundle-analyzer'
import { withSentryConfig } from '@sentry/nextjs'
import nextPWA from 'next-pwa'

// Replicate __dirname for ES Modules
const __filename = fileURLToPath(import.meta.url)
const __dirname = path.dirname(__filename)

// Instantiate wrappers using imported functions
const withBundleAnalyzer = nextBundleAnalyzer({
  enabled: process.env.ANALYZE === 'true',
})
const withPWA = nextPWA({
  dest: 'public',
})

// Constants remain the same
const IS_DEV = process.env.NODE_ENV === 'development'
const IS_DOCKER = process.env.DOCKER

/**
 * @type {import('@sentry/nextjs').SentryWebpackPluginOptions}
 **/
const sentryWebpackPluginOptions = {
  silent: true,
}

// H-20: ベースの Content Security Policy。
// ePub 描画時に iframe 内 inline script を許容しているため `script-src 'self' 'unsafe-inline'` だが、
// 将来的には CSP nonce + sandbox 強化（CR-5）で `'unsafe-inline'` を取り除くこと。
const buildCsp = () => {
  const apiOrigin =
    process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000'
  const directives = [
    "default-src 'self'",
    "base-uri 'self'",
    "frame-ancestors 'none'",
    "object-src 'none'",
    "form-action 'self'",
    "img-src 'self' data: blob: https:",
    "media-src 'self' blob: https:",
    "font-src 'self' data: https:",
    "style-src 'self' 'unsafe-inline'",
    `connect-src 'self' ${apiOrigin} https: wss:`,
    "worker-src 'self' blob:",
    // Sentry / Next.js dev で必要な inline / eval は dev 限定で許容。
    IS_DEV
      ? "script-src 'self' 'unsafe-inline' 'unsafe-eval'"
      : "script-src 'self' 'unsafe-inline'",
  ]
  return directives.join('; ')
}

const securityHeaders = [
  // H-20: 主要セキュリティヘッダー
  { key: 'Content-Security-Policy', value: buildCsp() },
  { key: 'X-Frame-Options', value: 'DENY' },
  { key: 'X-Content-Type-Options', value: 'nosniff' },
  { key: 'Referrer-Policy', value: 'strict-origin-when-cross-origin' },
  {
    key: 'Permissions-Policy',
    value: 'camera=(), microphone=(), geolocation=(), interest-cohort=()',
  },
  {
    key: 'Strict-Transport-Security',
    value: 'max-age=63072000; includeSubDomains; preload',
  },
  { key: 'Cross-Origin-Opener-Policy', value: 'same-origin' },
  { key: 'X-DNS-Prefetch-Control', value: 'off' },
]

/**
 * @type {import('next').NextConfig}
 **/
const config = {
  pageExtensions: ['ts', 'tsx'],
  webpack(config) {
    return config
  },
  i18n: {
    locales: ['en-US', 'cmn-CN', 'ja-JP'],
    defaultLocale: 'en-US',
  },
  transpilePackages: [
    '@flow/internal',
    '@flow/epubjs',
    '@material/material-color-utilities',
  ],
  poweredByHeader: false,
  async headers() {
    return [
      {
        source: '/:path*',
        headers: securityHeaders,
      },
    ]
  },
  ...(IS_DOCKER && {
    output: 'standalone',
    experimental: {
      outputFileTracingRoot: path.join(__dirname, '../../'),
    },
  }),
}

// Apply wrappers - logic remains the same
const baseConfig = withPWA(withBundleAnalyzer(config))

const dev = baseConfig
const docker = baseConfig
const prod = withSentryConfig(baseConfig, sentryWebpackPluginOptions)

export default IS_DEV ? dev : IS_DOCKER ? docker : prod
