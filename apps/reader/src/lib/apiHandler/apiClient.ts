import { getAccessToken } from '../auth/token'

import { throwApiError, unwrapApiResponse } from './responseParser'

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL

interface ApiClientOptions extends Omit<RequestInit, 'body'> {
  params?: Record<string, string | number | boolean>
  body?: unknown
}

// CR-1: 認証トークンの取得経路。
// 1) `getAuthToken` が登録されていればそれを優先（Supabase Auth クライアントから登録する想定）
// 2) `lib/auth/token.ts` 経由の localStorage 値
// 3) 取得できなければ未認証のまま送信（バックエンドが `auth_dev_bypass` 設定でテストユーザーを返す）
type AuthTokenProvider = () => string | null | Promise<string | null>

let authTokenProvider: AuthTokenProvider | null = null

export function setAuthTokenProvider(provider: AuthTokenProvider | null) {
  authTokenProvider = provider
}

async function resolveAuthToken(): Promise<string | null> {
  if (authTokenProvider) {
    try {
      const token = await authTokenProvider()
      if (token) return token
    } catch (error) {
      console.warn('Auth token provider threw:', error)
    }
  }
  return getAccessToken()
}

/**
 * A generic API client function to handle requests to the backend.
 * Automatically adds base URL, common headers, Bearer token, and handles JSON responses/errors.
 */
export async function apiClient<T>(
  endpoint: string,
  options: ApiClientOptions = {},
): Promise<T> {
  if (!API_BASE_URL) {
    throw new Error(
      'NEXT_PUBLIC_API_BASE_URL is not defined. Please check your environment variables.',
    )
  }

  const url = new URL(`${API_BASE_URL}${endpoint}`)

  // CR-4 後: クエリに固定 user_id を付与しない。
  Object.entries(options.params || {}).forEach(([key, value]) => {
    if (value !== undefined && value !== null) {
      url.searchParams.append(key, String(value))
    }
  })

  const { params, body, headers: customHeaders, ...fetchOptions } = options

  const headers = new Headers(customHeaders)

  // CR-1: Bearer Token を Authorization ヘッダで送る。
  // 呼出側が渡した Authorization は set() でこちらの値に上書きされる。
  const token = await resolveAuthToken()
  if (token) {
    headers.set('Authorization', `Bearer ${token}`)
  } else {
    headers.delete('Authorization')
  }

  let requestBody: BodyInit | null = null
  if (body !== undefined && body !== null) {
    if (
      body instanceof FormData ||
      body instanceof URLSearchParams ||
      typeof body === 'string' ||
      body instanceof Blob ||
      body instanceof ArrayBuffer
    ) {
      requestBody = body
    } else if (typeof body === 'object') {
      requestBody = JSON.stringify(body)
      if (!headers.has('Content-Type')) {
        headers.set('Content-Type', 'application/json')
      }
    }
  }

  const response = await fetch(url.toString(), {
    ...fetchOptions,
    headers,
    body: requestBody,
    credentials: 'omit',
  })

  if (!response.ok) {
    await throwApiError(response)
  }

  try {
    return await unwrapApiResponse<T>(response)
  } catch (err) {
    console.error(`API Logic Error: ${endpoint}`, err)
    throw err
  }
}
