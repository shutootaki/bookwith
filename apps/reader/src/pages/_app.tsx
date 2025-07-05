'use client'

import './styles.css'
import 'react-photo-view/dist/react-photo-view.css'

import { LiteralProvider } from '@literal-ui/core'
import { ErrorBoundary } from '@sentry/nextjs'
import type { AppProps } from 'next/app'
import { useRouter } from 'next/router'

import { Layout, Theme } from '../components'
import { GlobalLoadingOverlay } from '../components/GlobalLoadingOverlay'

export const TEST_USER_ID = '91527c9d-48aa-41d0-bb85-dc96f26556a0'

export default function MyApp({ Component, pageProps }: AppProps) {
  const router = useRouter()

  if (router.pathname === '/success') return <Component {...pageProps} />

  return (
    <ErrorBoundary fallback={<Fallback />}>
      {/* @ts-ignore */}
      <LiteralProvider>
        <Theme />
        <Layout>
          <Component {...pageProps} />
        </Layout>
        <GlobalLoadingOverlay />
      </LiteralProvider>
    </ErrorBoundary>
  )
}

const Fallback: React.FC = () => {
  return <div>Something went wrong.</div>
}
