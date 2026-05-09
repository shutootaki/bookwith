// localStorage に集約することで、apiClient / fetcher / SSE 経路すべてに同じ Bearer Token が流れるようにする。

const ACCESS_TOKEN_KEY = 'bookwith.access_token'
const REFRESH_TOKEN_KEY = 'bookwith.refresh_token'

function getStorageItem(key: string): string | null {
  if (typeof window === 'undefined') return null
  try {
    return window.localStorage.getItem(key)
  } catch {
    return null
  }
}

function setStorageItem(key: string, value: string | null): void {
  if (typeof window === 'undefined') return
  try {
    if (value) {
      window.localStorage.setItem(key, value)
    } else {
      window.localStorage.removeItem(key)
    }
  } catch {
    // localStorage unavailable
  }
}

export const getAccessToken = () => getStorageItem(ACCESS_TOKEN_KEY)

export const setAccessToken = (token: string | null) =>
  setStorageItem(ACCESS_TOKEN_KEY, token)

export function getRefreshToken(): string | null {
  return getStorageItem(REFRESH_TOKEN_KEY)
}

export function setRefreshToken(token: string | null): void {
  setStorageItem(REFRESH_TOKEN_KEY, token)
}

export function clearAuthTokens(): void {
  setAccessToken(null)
  setRefreshToken(null)
}

export interface AuthSessionLike {
  access_token?: string | null
  refresh_token?: string | null
}

export function persistAuthSession(session: AuthSessionLike | null): void {
  if (!session) {
    clearAuthTokens()
    return
  }
  setAccessToken(session.access_token ?? null)
  setRefreshToken(session.refresh_token ?? null)
}

// apiClient を経由しない経路 (SSE ストリーム等) でも同じ Authorization ヘッダを組み立てるための共通ヘルパー。
export function buildAuthHeaders(
  base: Record<string, string> = {},
): Record<string, string> {
  const headers: Record<string, string> = { ...base }
  const token = getAccessToken()
  if (token) headers.Authorization = `Bearer ${token}`
  return headers
}
