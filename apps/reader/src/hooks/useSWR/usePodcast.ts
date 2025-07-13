import useSWR from 'swr'

import { components } from '../../lib/openapi-schema/schema'

import { fetcher } from './fetcher'

type PodcastListResponse = components['schemas']['PodcastListResponse']

/**
 * Hook to fetch podcasts for a specific book
 * @param bookId The ID of the book to get podcasts for
 * @returns SWR hook result with podcasts data
 */
export function usePodcastsByBook(bookId: string | undefined) {
  const { data, error, mutate } = useSWR<PodcastListResponse>(
    bookId
      ? `${process.env.NEXT_PUBLIC_API_BASE_URL}/podcasts/book/${bookId}`
      : null,
    fetcher,
    {
      revalidateOnFocus: false,
      revalidateOnReconnect: false,
    },
  )

  return {
    podcasts: data?.podcasts || [],
    isLoading: !error && !data,
    error,
    mutate,
  }
}
