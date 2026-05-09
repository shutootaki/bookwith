import { clearAuthTokens } from '../auth/token'

export type ApiError = Error & { status: number }

export function makeApiError(message: string, status: number): ApiError {
  const err = new Error(message) as ApiError
  err.status = status
  return err
}

export function handleUnauthorized(status: number): void {
  if (status === 401) clearAuthTokens()
}

async function readErrorMessage(res: Response): Promise<string> {
  try {
    const json = await res.clone().json()
    if (typeof json?.detail === 'string') return json.detail
    if (typeof json?.error === 'string') return json.error
  } catch {
    // fall through to text/status
  }
  const text = await res.text().catch(() => '')
  return text || `Request failed with status ${res.status} ${res.statusText}`
}

export async function throwApiError(res: Response): Promise<never> {
  handleUnauthorized(res.status)
  throw makeApiError(await readErrorMessage(res), res.status)
}

export async function unwrapApiResponse<T>(res: Response): Promise<T> {
  if (res.status === 204 || res.headers.get('content-length') === '0') {
    return undefined as T
  }
  const data = await res.json()
  if (data && typeof data === 'object' && typeof data.success === 'boolean') {
    if (data.success) return data.data as T
    const message =
      typeof data.error === 'string'
        ? data.error
        : 'API returned an unspecified error'
    throw makeApiError(message, res.status)
  }
  return data as T
}
