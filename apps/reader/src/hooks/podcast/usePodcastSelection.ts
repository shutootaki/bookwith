import { useEffect, useState } from 'react'

import { PodcastResponse } from '../../types/podcast'
import { findPodcastByStatus } from '../../utils/podcast'

interface UsePodcastSelectionParams {
  podcasts: PodcastResponse[]
  bookId?: string
}

interface UsePodcastSelectionReturn {
  selectedPodcast: PodcastResponse | null
  setSelectedPodcast: (podcast: PodcastResponse | null) => void
}

/**
 * ポッドキャストの自動選択ロジックを管理するカスタムフック
 * 優先順位: 完了 > 処理中 > 失敗
 */
export const usePodcastSelection = ({
  podcasts,
  bookId,
}: UsePodcastSelectionParams): UsePodcastSelectionReturn => {
  const [selectedPodcast, setSelectedPodcast] =
    useState<PodcastResponse | null>(null)

  // 本が切り替わったときにselectedPodcastをリセット
  useEffect(() => {
    setSelectedPodcast(null)
  }, [bookId])

  // 自動的に最初の利用可能なポッドキャストを選択
  useEffect(() => {
    if (
      podcasts.length > 0 &&
      (!selectedPodcast || selectedPodcast.book_id !== bookId)
    ) {
      // 完了したポッドキャストを優先
      const completedPodcast = findPodcastByStatus(podcasts, 'COMPLETED')
      if (completedPodcast && completedPodcast.audio_url) {
        setSelectedPodcast(completedPodcast)
        return
      }

      // 処理中のポッドキャストがあれば選択
      const processingPodcast = findPodcastByStatus(podcasts, 'PROCESSING')
      if (processingPodcast) {
        setSelectedPodcast(processingPodcast)
        return
      }

      // 失敗したポッドキャストがあれば選択
      const failedPodcast = findPodcastByStatus(podcasts, 'FAILED')
      if (failedPodcast) {
        setSelectedPodcast(failedPodcast)
        return
      }
    }
  }, [podcasts, selectedPodcast, bookId])

  return {
    selectedPodcast,
    setSelectedPodcast,
  }
}
