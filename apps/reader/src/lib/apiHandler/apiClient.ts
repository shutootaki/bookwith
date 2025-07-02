import { TEST_USER_ID } from '../../pages/_app'

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL

interface ApiClientOptions extends Omit<RequestInit, 'body'> {
  params?: Record<string, string | number | boolean>
  body?: any
}

/**
 * A generic API client function to handle requests to the backend.
 * Automatically adds base URL, common headers, user ID param, and handles JSON responses/errors.
 * @param endpoint The API endpoint path (e.g., '/books').
 * @param options Request options including method, body, params, headers, etc.
 * @returns The 'data' field from the API response.
 * @throws Throws an error if the request fails or the API returns an error.
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

  const defaultParams: Record<string, string> = { user_id: TEST_USER_ID }
  const queryParams = { ...defaultParams, ...(options.params || {}) }
  Object.entries(queryParams).forEach(([key, value]) => {
    if (value !== undefined && value !== null) {
      url.searchParams.append(key, String(value))
    }
  })

  const { params, body, headers: customHeaders, ...fetchOptions } = options

  const headers = new Headers(customHeaders)

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

  try {
    const response = await fetch(url.toString(), {
      ...fetchOptions,
      headers,
      body: requestBody,
    })

    if (!response.ok) {
      let errorData: any = {
        message: `Request failed with status ${response.status} ${response.statusText}`,
      }
      try {
        const errorJson = await response.json()
        errorData = errorJson?.error || errorJson?.message || errorJson
      } catch {
        errorData.responseBody = await response.text()
      }
      console.error(`API Error (${response.status}): ${endpoint}`, errorData)

      throw new Error(
        typeof errorData === 'string'
          ? errorData
          : errorData.message || JSON.stringify(errorData),
      )
    }

    if (
      response.status === 204 ||
      response.headers.get('content-length') === '0'
    ) {
      return undefined as T
    }

    const responseData = await response.json()

    if (responseData && typeof responseData.success === 'boolean') {
      if (responseData.success) {
        return responseData.data as T
      } else {
        const errorMessage =
          responseData.error || 'API returned an unspecified error'
        console.error(`API Logic Error: ${endpoint}`, errorMessage)
        throw new Error(errorMessage)
      }
    }

    console.warn(
      `API response for ${endpoint} did not match standard wrapper format.`,
      responseData,
    )
    return responseData as T
  } catch (error) {
    console.error(`API Request Failed: ${endpoint}`, error)

    if (error instanceof Error) {
      throw error
    } else {
      throw new Error('An unknown error occurred during the API request.')
    }
  }
}
