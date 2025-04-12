import useSWR from 'swr'

// バックエンドのBookBase型に合わせた型定義
interface BookBase {
  id: string
  name: string
  author?: string
  size: number
  percentage: number
  cfi?: string
  has_cover: boolean
}

// APIレスポンスの型
interface BooksResponse {
  success: boolean
  data: BookBase[]
  count: number
  message?: string
}

export function useLibrary() {
  const { data, error } = useSWR<BooksResponse>(
    `${process.env.NEXT_PUBLIC_API_BASE_URL}/books`,
    async (url) => {
      const response = await fetch(url)
      if (!response.ok) {
        throw new Error('書籍の取得に失敗しました')
      }
      return response.json()
    },
  )

  return data?.data || []
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
  return useSWR<CoversResponse>(
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
}
