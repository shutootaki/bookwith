const path = require('path')

const withBundleAnalyzer = require('@next/bundle-analyzer')({
  enabled: process.env.ANALYZE === 'true',
})
const { withSentryConfig } = require('@sentry/nextjs')
const withPWA = require('next-pwa')({
  dest: 'public',
})

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
const config = {
  pageExtensions: ['ts', 'tsx'],
  webpack(config) {
    return config
  },
  i18n: {
    locales: ['en-US', 'zh-CN'],
    defaultLocale: 'en-US',
  },
  // トランスパイルするパッケージのリストを直接指定
  transpilePackages: [
    '@flow/internal',
    '@flow/epubjs',
    '@material/material-color-utilities',
  ],
  reactStrictMode: true,
  poweredByHeader: false,
  ...(IS_DOCKER && {
    output: 'standalone',
    experimental: {
      outputFileTracingRoot: path.join(__dirname, '../../'),
    },
  }),
}

const baseConfig = withPWA(withBundleAnalyzer(config))

const dev = baseConfig
const docker = baseConfig
const prod = withSentryConfig(
  baseConfig,
  // Make sure adding Sentry options is the last code to run before exporting, to
  // ensure that your source maps include changes from all other Webpack plugins
  sentryWebpackPluginOptions,
)

module.exports = IS_DEV ? dev : IS_DOCKER ? docker : prod
