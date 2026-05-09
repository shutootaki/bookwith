import {
  throwApiError,
  unwrapApiResponse,
} from '../../lib/apiHandler/responseParser'
import { buildAuthHeaders } from '../../lib/auth/token'

export async function fetcher<JSON = never>(
  input: RequestInfo,
  init?: RequestInit,
): Promise<JSON> {
  const headers = new Headers(init?.headers)
  // CR-1: SWR 経由の fetch も Bearer Token を付与する (呼出側が指定済みなら尊重)。
  if (!headers.has('Authorization')) {
    const auth = buildAuthHeaders()
    if (auth.Authorization) headers.set('Authorization', auth.Authorization)
  }

  const res = await fetch(input, {
    ...init,
    headers,
    credentials: 'omit',
  })

  if (!res.ok) {
    await throwApiError(res)
  }

  return unwrapApiResponse<JSON>(res)
}
