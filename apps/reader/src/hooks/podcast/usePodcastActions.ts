import { useRouter } from 'next/router'
import { useState } from 'react'
import { toast } from 'sonner'
import { mutate as globalMutate } from 'swr'

import {
  createPodcast,
  getPodcastById,
  pollPodcastStatus,
  retryPodcast,
} from '../../lib/apiHandler/podcastApiHandler'
import { useTranslation } from '../useTranslation'

import { usePodcastError } from './usePodcastError'

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
  const { locale = 'en-US' } = useRouter()
  const [isCreating, setIsCreating] = useState(false)
  const [retryingPodcastId, setRetryingPodcastId] = useState<string | null>(
    null,
  )
  const { setError, clearError } = usePodcastError()

  /**
   * 成功通知
   */
  const notifySuccess = (operation: 'create' | 'retry'): void => {
    const successKey = {
      create: 'podcast.pane.generation_started',
      retry: 'podcast.pane.regeneration_started',
    }[operation]
    toast.success(t(successKey))
  }

  const handleCreatePodcast = async (
    bookId: string,
    bookName: string,
  ): Promise<boolean> => {
    clearError()
    setIsCreating(true)
    try {
      const title = `${bookName}のポッドキャスト`
      const result = await createPodcast(bookId, locale, title)
      if (result) {
        notifySuccess('create')
        if (result.status === 'PROCESSING' || result.status === 'PENDING') {
          pollPodcastStatus(
            result.id,
            (status) => {
              if (status.status === 'COMPLETED' || status.status === 'FAILED') {
                globalMutate(
                  `${process.env.NEXT_PUBLIC_API_BASE_URL}/podcasts/book/${bookId}`,
                )
              }
            },
            5000,
          )
        }
        return true
      } else {
        setError(new Error('Creation failed'))
        return false
      }
    } catch (error) {
      setError(error)
      return false
    } finally {
      setIsCreating(false)
    }
  }

  const handleRetryPodcast = async (podcastId: string): Promise<boolean> => {
    clearError()
    setRetryingPodcastId(podcastId)
    try {
      const result = await retryPodcast(podcastId)
      if (result) {
        notifySuccess('retry')
        const existingPodcast = await getPodcastById(podcastId)
        const bookId = existingPodcast?.book_id
        if (
          (result.status === 'PROCESSING' || result.status === 'PENDING') &&
          bookId
        ) {
          pollPodcastStatus(
            result.id,
            (status) => {
              if (status.status === 'COMPLETED' || status.status === 'FAILED') {
                globalMutate(
                  `${process.env.NEXT_PUBLIC_API_BASE_URL}/podcasts/book/${bookId}`,
                )
              }
            },
            5000,
          )
        }
        return true
      } else {
        setError(new Error('Retry failed'))
        return false
      }
    } catch (error) {
      setError(error)
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
