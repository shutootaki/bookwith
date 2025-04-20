import { Annotation } from '@flow/epubjs/types/annotations'
import { PackagingMetadataObject } from '@flow/epubjs/types/packaging'
import useSWR from 'swr'
import { TypographyConfiguration } from '../state'

export interface BookDetail {
  id: string
  annotations: Annotation[]
  author?: string
  book_metadata: PackagingMetadataObject
  cfi?: string
  configuration?: { typography?: TypographyConfiguration }
  cover_path: string | null
  definitions: string[]
  has_cover: boolean
  name: string
  percentage?: number
  size: number
  tenant_id: string | null
  created_at: number
  updated_at: number
}

interface BooksResponse {
  success: boolean
  data: BookDetail[]
  count: number
  message?: string
}

export function useLibrary() {
  const { data, error, mutate } = useSWR<BooksResponse>(
    `${process.env.NEXT_PUBLIC_API_BASE_URL}/books`,
    async (url) => {
      const response = await fetch(url)
      if (!response.ok) {
        throw new Error('書籍の取得に失敗しました')
      }
      return response.json()
    },
  )

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
