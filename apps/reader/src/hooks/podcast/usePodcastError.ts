import { useCallback, useState } from 'react'

import { PODCAST_ERROR_KEYS } from '../../constants/podcast'
import { getPodcastErrorKey } from '../../utils/podcast'
import { useTranslation } from '../useTranslation'

interface UsePodcastErrorReturn {
  error: string | null
  setError: (error: unknown) => void
  clearError: () => void
  getErrorMessage: (errorKey: string) => string
}

/**
 * ポッドキャストコンポーネントでのエラーハンドリングを管理するフック
 */
export const usePodcastError = (): UsePodcastErrorReturn => {
  const t = useTranslation()
  const [error, setErrorState] = useState<string | null>(null)

  const getErrorMessage = useCallback(
    (errorKey: string): string => {
      switch (errorKey) {
        case PODCAST_ERROR_KEYS.GENERATION_FAILED:
          return t('podcast.errors.generation_failed')
        case PODCAST_ERROR_KEYS.PLAYBACK_FAILED:
          return t('podcast.errors.playback_failed')
        case PODCAST_ERROR_KEYS.NETWORK_ERROR:
          return t('podcast.errors.network_error')
        case PODCAST_ERROR_KEYS.LOADING_FAILED:
          return t('podcast.errors.loading_failed')
        default:
          return t('podcast.errors.unknown')
      }
    },
    [t],
  )

  const setError = useCallback(
    (error: unknown) => {
      const errorKey = getPodcastErrorKey(error)
      const message = getErrorMessage(errorKey)
      setErrorState(message)

      // コンソールにエラーをログ出力
      console.error('[Podcast Error]', error)
    },
    [getErrorMessage],
  )

  const clearError = useCallback(() => {
    setErrorState(null)
  }, [])

  return {
    error,
    setError,
    clearError,
    getErrorMessage,
  }
}
