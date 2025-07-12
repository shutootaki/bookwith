import { useState } from 'react'

import {
  createPodcast,
  retryPodcast,
} from '../lib/apiHandler/podcastApiHandler'
import {
  generatePodcastTitle,
  handlePodcastError,
  notifyPodcastSuccess,
} from '../utils/podcast'

import { useTranslation } from './useTranslation'

export interface UsePodcastActionsReturn {
  isCreating: boolean
  retryingPodcastId: string | null
  createPodcast: (bookId: string, bookName: string) => Promise<boolean>
  retryPodcastGeneration: (podcastId: string) => Promise<boolean>
}

/**
 * ポッドキャストの作成・再試行アクションを管理するカスタムフック
 */
export const usePodcastActions = (): UsePodcastActionsReturn => {
  const t = useTranslation()
  const [isCreating, setIsCreating] = useState(false)
  const [retryingPodcastId, setRetryingPodcastId] = useState<string | null>(
    null,
  )

  const handleCreatePodcast = async (
    bookId: string,
    bookName: string,
  ): Promise<boolean> => {
    setIsCreating(true)
    try {
      const result = await createPodcast(bookId, generatePodcastTitle(bookName))

      if (result) {
        notifyPodcastSuccess('create', t)
        return true
      } else {
        handlePodcastError(new Error('Creation failed'), 'create', t)
        return false
      }
    } catch (error) {
      handlePodcastError(error, 'create', t)
      return false
    } finally {
      setIsCreating(false)
    }
  }

  const handleRetryPodcast = async (podcastId: string): Promise<boolean> => {
    setRetryingPodcastId(podcastId)
    try {
      const result = await retryPodcast(podcastId)

      if (result) {
        notifyPodcastSuccess('retry', t)
        return true
      } else {
        handlePodcastError(new Error('Retry failed'), 'retry', t)
        return false
      }
    } catch (error) {
      handlePodcastError(error, 'retry', t)
      return false
    } finally {
      setRetryingPodcastId(null)
    }
  }

  return {
    isCreating,
    retryingPodcastId,
    createPodcast: handleCreatePodcast,
    retryPodcastGeneration: handleRetryPodcast,
  }
}
