import useSWR from 'swr'

import { components } from '../lib/openapi-schema/schema'

export function useLibrary() {
  const { data, error, mutate } = useSWR<
    components['schemas']['BooksResponse']
  >(`${process.env.NEXT_PUBLIC_API_BASE_URL}/books`, async (url) => {
    const response = await fetch(url)
    if (!response.ok) {
      throw new Error('書籍の取得に失敗しました')
    }
    return response.json()
  })

  return {
    books: data?.data || [],
    error,
    mutate,
  }
}

export interface CoverData {
  book_id: string
  title: string
  cover_url: string
}

export interface CoversResponse {
  success: boolean
  data: CoverData[]
}

export function useRemoteCovers() {
  const { data, mutate } = useSWR<CoversResponse>(
    `${process.env.NEXT_PUBLIC_API_BASE_URL}/books/covers`,
    async (url) => {
      const response = await fetch(url)
      if (!response.ok) {
        throw new Error('Failed to fetch book covers')
      }
      return response.json()
    },
    {
      shouldRetryOnError: false,
    },
  )
  return {
    covers: data || { success: false, data: [] },
    mutate,
  }
}
