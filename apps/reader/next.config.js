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
  // Additional config options for the Sentry Webpack plugin. Keep in mind that
  // the following options are set automatically, and overriding them is not
  // recommended:
  //   release, url, org, project, authToken, configFile, stripPrefix,
  //   urlPrefix, include, ignore

  silent: true, // Suppresses all logs
  // For all available options, see:
  // https://github.com/getsentry/sentry-webpack-plugin#options.
}

/**
 * @type {import('next').NextConfig}
 **/
// Base Next.js config object remains the same structure
const config = {
  pageExtensions: ['ts', 'tsx'],
  webpack(config) {
    // Webpack function usually doesn't need changes for ESM vs CJS
    return config
  },
  i18n: {
    locales: ['en-US', 'zh-CN'],
    defaultLocale: 'en-US',
  },
  transpilePackages: [
    '@flow/internal',
    '@flow/epubjs',
    '@material/material-color-utilities',
  ],
  poweredByHeader: false,
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
const docker = baseConfig // Note: Sentry is not applied in the docker case here
const prod = withSentryConfig(
  baseConfig,
  // Make sure adding Sentry options is the last code to run before exporting, to
  // ensure that your source maps include changes from all other Webpack plugins
  sentryWebpackPluginOptions,
)

// Use export default instead of module.exports
export default IS_DEV ? dev : IS_DOCKER ? docker : prod
