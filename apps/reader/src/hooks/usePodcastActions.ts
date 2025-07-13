import { useRouter } from 'next/router'
import { useState } from 'react'
import { toast } from 'sonner'
import { mutate as globalMutate } from 'swr'

import {
  createPodcast,
  retryPodcast,
  pollPodcastStatus,
} from '../lib/apiHandler/podcastApiHandler'

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
  const { locale = 'en-US' } = useRouter()
  const [isCreating, setIsCreating] = useState(false)
  const [retryingPodcastId, setRetryingPodcastId] = useState<string | null>(
    null,
  )

  /**
   * エラーハンドリング
   */
  const handleError = (error: unknown, operation: 'create' | 'retry'): void => {
    console.error(`Error during podcast ${operation}:`, error)

    const errorKey = {
      create: 'podcast.pane.generation_failed',
      retry: 'podcast.pane.regeneration_failed',
    }[operation]

    toast.error(t(errorKey))
  }

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
    setIsCreating(true)
    try {
      const title = `${bookName}のポッドキャスト`
      const result = await createPodcast(bookId, locale, title)

      if (result) {
        notifySuccess('create')
        // statusがPROCESSINGまたはPENDINGのときのみポーリング
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
            5000, // 5秒間隔
          )
        }
        return true
      } else {
        handleError(new Error('Creation failed'), 'create')
        return false
      }
    } catch (error) {
      handleError(error, 'create')
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
        notifySuccess('retry')
        return true
      } else {
        handleError(new Error('Retry failed'), 'retry')
        return false
      }
    } catch (error) {
      handleError(error, 'retry')
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
