import { components } from '../openapi-schema/schema'

import { apiClient } from './apiClient'

// Type definitions from OpenAPI schema
type CreatePodcastRequest = components['schemas']['CreatePodcastRequest']
type CreatePodcastResponse = components['schemas']['CreatePodcastResponse']
type PodcastResponse = components['schemas']['PodcastResponse']
type PodcastListResponse = components['schemas']['PodcastListResponse']
type PodcastStatusResponse = components['schemas']['PodcastStatusResponse']
type PodcastLanguage = components['schemas']['PodcastLanguage']

/**
 * Creates a new podcast for a book
 * @param bookId The ID of the book to create podcast for
 * @param title Custom title for the podcast (optional)
 * @param language Language code for the podcast (optional, defaults to en-US)
 * @returns A promise that resolves to the created podcast response
 */
export async function createPodcast(
  bookId: string,
  language: string,
  title?: string,
): Promise<CreatePodcastResponse | null> {
  try {
    const requestBody: CreatePodcastRequest = {
      book_id: bookId,
      title,
      language: language as PodcastLanguage,
    }

    const responseData = await apiClient<CreatePodcastResponse>('/podcasts', {
      method: 'POST',
      body: requestBody,
    })

    return responseData
  } catch (error) {
    console.error('Error creating podcast:', error)
    return null
  }
}

/**
 * Gets a podcast by ID
 * @param podcastId The ID of the podcast to retrieve
 * @returns A promise that resolves to the podcast response
 */
export async function getPodcastById(
  podcastId: string,
): Promise<PodcastResponse | null> {
  try {
    const responseData = await apiClient<PodcastResponse>(
      `/podcasts/${podcastId}`,
      {
        method: 'GET',
      },
    )

    return responseData
  } catch (error) {
    console.error(`Error getting podcast ${podcastId}:`, error)
    return null
  }
}

/**
 * Gets all podcasts for a specific book
 * @param bookId The ID of the book to get podcasts for
 * @returns A promise that resolves to the podcast list response
 */
export async function getPodcastsByBook(
  bookId: string,
): Promise<PodcastResponse[]> {
  try {
    const responseData = await apiClient<PodcastListResponse>(
      `/podcasts/book/${bookId}`,
      {
        method: 'GET',
      },
    )

    return responseData?.podcasts || []
  } catch (error) {
    console.error(`Error getting podcasts for book ${bookId}:`, error)
    return []
  }
}

/**
 * Gets the status of a podcast generation
 * @param podcastId The ID of the podcast to check status for
 * @returns A promise that resolves to the podcast status response
 */
export async function getPodcastStatus(
  podcastId: string,
): Promise<PodcastStatusResponse | null> {
  try {
    const responseData = await apiClient<PodcastStatusResponse>(
      `/podcasts/${podcastId}/status`,
      {
        method: 'GET',
      },
    )

    return responseData
  } catch (error) {
    console.error(`Error getting podcast status ${podcastId}:`, error)
    return null
  }
}

/**
 * Retries a failed podcast generation
 * @param podcastId The ID of the podcast to retry
 * @returns A promise that resolves to the retry response
 */
export async function retryPodcast(
  podcastId: string,
): Promise<CreatePodcastResponse | null> {
  console.log('retryPodcast', podcastId)
  try {
    const responseData = await apiClient<CreatePodcastResponse>(
      `/podcasts/${podcastId}/retry`,
      {
        method: 'POST',
      },
    )

    return responseData
  } catch (error) {
    console.error(`Error retrying podcast ${podcastId}:`, error)
    return null
  }
}

/**
 * Polls for podcast status updates until completion or failure
 * @param podcastId The ID of the podcast to poll
 * @param onUpdate Callback function called on each status update
 * @param intervalMs Polling interval in milliseconds (default: 2000)
 * @param timeoutMs Maximum time to poll in milliseconds (default: 300000 - 5 minutes)
 * @returns A promise that resolves when the podcast is completed or fails
 */
export async function pollPodcastStatus(
  podcastId: string,
  onUpdate?: (status: PodcastStatusResponse) => void,
  intervalMs: number = 2000,
  timeoutMs: number = 300000,
): Promise<PodcastStatusResponse | null> {
  const startTime = Date.now()

  return new Promise((resolve) => {
    const poll = async () => {
      try {
        const status = await getPodcastStatus(podcastId)

        if (!status) {
          resolve(null)
          return
        }

        onUpdate?.(status)

        // Check if completed or failed
        if (status.status === 'COMPLETED' || status.status === 'FAILED') {
          resolve(status)
          return
        }

        // Check timeout
        if (Date.now() - startTime > timeoutMs) {
          console.warn(`Podcast status polling timed out for ${podcastId}`)
          resolve(status)
          return
        }

        // Continue polling
        setTimeout(poll, intervalMs)
      } catch (error) {
        console.error('Error during podcast status polling:', error)
        resolve(null)
      }
    }

    poll()
  })
}
