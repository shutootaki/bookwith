import useSWR from 'swr'

import { components } from '../../lib/openapi-schema/schema'
import { getPodcastById, getPodcastsByBook, getPodcastStatus } from '../../lib/apiHandler/podcastApiHandler'

import { fetcher } from './fetcher'

// Type definitions
type PodcastResponse = components['schemas']['PodcastResponse']
type PodcastStatusResponse = components['schemas']['PodcastStatusResponse']
type PodcastListResponse = components['schemas']['PodcastListResponse']

/**
 * Hook to fetch podcasts for a specific book
 * @param bookId The ID of the book to get podcasts for
 * @returns SWR hook result with podcasts data
 */
export function usePodcastsByBook(bookId: string | undefined) {
  const { data, error, mutate } = useSWR<PodcastListResponse>(
    bookId ? `${process.env.NEXT_PUBLIC_API_BASE_URL}/podcasts/book/${bookId}` : null,
    fetcher,
    {
      revalidateOnFocus: false,
      revalidateOnReconnect: false,
    }
  )

  return {
    podcasts: data?.podcasts || [],
    isLoading: !error && !data,
    error,
    mutate,
  }
}

/**
 * Hook to fetch a specific podcast by ID
 * @param podcastId The ID of the podcast to fetch
 * @returns SWR hook result with podcast data
 */
export function usePodcast(podcastId: string | undefined) {
  const { data, error, mutate } = useSWR<PodcastResponse>(
    podcastId ? `${process.env.NEXT_PUBLIC_API_BASE_URL}/podcasts/${podcastId}` : null,
    fetcher,
    {
      revalidateOnFocus: false,
      revalidateOnReconnect: false,
    }
  )

  return {
    podcast: data || null,
    isLoading: !error && !data,
    error,
    mutate,
  }
}

/**
 * Hook to fetch podcast status with automatic polling for in-progress podcasts
 * @param podcastId The ID of the podcast to check status for
 * @param enablePolling Whether to enable automatic polling (default: true)
 * @param pollingInterval Polling interval in milliseconds (default: 2000)
 * @returns SWR hook result with podcast status data
 */
export function usePodcastStatus(
  podcastId: string | undefined,
  enablePolling: boolean = true,
  pollingInterval: number = 2000,
) {
  const { data, error, mutate } = useSWR<PodcastStatusResponse>(
    podcastId ? `${process.env.NEXT_PUBLIC_API_BASE_URL}/podcasts/${podcastId}/status` : null,
    fetcher,
    {
      revalidateOnFocus: false,
      revalidateOnReconnect: false,
      refreshInterval: (data: PodcastStatusResponse | undefined) => {
        return enablePolling && data?.status === 'PROCESSING' ? pollingInterval : 0
      },
    }
  )

  return {
    status: data || null,
    isLoading: !error && !data,
    error,
    mutate,
  }
}

/**
 * Hook to get podcast creation status for a book
 * This checks if a podcast exists for the given book and returns its status
 * @param bookId The ID of the book to check podcast status for
 * @returns Information about podcast availability and status
 */
export function usePodcastAvailability(bookId: string | undefined) {
  const { podcasts, isLoading, error } = usePodcastsByBook(bookId)

  // Get the first podcast for the book (assuming one podcast per book)
  const podcast = podcasts.length > 0 ? podcasts[0] : null

  return {
    hasPodcast: !!podcast,
    podcast,
    canCreatePodcast: !isLoading && !podcast,
    isLoading,
    error,
  }
}