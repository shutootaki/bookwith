import { RefreshCw } from 'lucide-react'
import React, { useCallback } from 'react'

import { usePodcastActions } from '../../hooks'
import { usePodcastSelection } from '../../hooks/podcast/usePodcastSelection'
import { usePodcastsByBook } from '../../hooks/useSWR/usePodcast'
import { useTranslation } from '../../hooks/useTranslation'
import { useReaderSnapshot } from '../../models'
import { Button } from '../ui/button'
import { Card } from '../ui/card'

import { LibraryPodcastView } from './LibraryPodcastView'
import { PodcastDetail } from './PodcastDetail'

export const PodcastPane: React.FC = () => {
  const t = useTranslation()
  const { focusedBookTab } = useReaderSnapshot()
  const {
    isCreating,
    createPodcast: createPodcastAction,
    retryPodcastGeneration,
    retryingPodcastId,
  } = usePodcastActions()

  const { podcasts, isLoading, error, mutate } = usePodcastsByBook(
    focusedBookTab?.book.id,
  )

  const { selectedPodcast } = usePodcastSelection({
    podcasts,
    bookId: focusedBookTab?.book.id,
  })

  const handleCreatePodcast = useCallback(async () => {
    if (!focusedBookTab?.book.id) return

    const success = await createPodcastAction(
      focusedBookTab.book.id,
      focusedBookTab.book.name,
    )
    if (success) {
      mutate() // Refresh the podcast list
    }
  }, [
    focusedBookTab?.book.id,
    focusedBookTab?.book.name,
    createPodcastAction,
    mutate,
  ])

  const handleRetryPodcast = useCallback(
    async (podcastId: string) => {
      try {
        await retryPodcastGeneration(podcastId)
        mutate() // リトライ後にリストをリフレッシュ
      } catch (error) {
        console.error('Failed to retry podcast:', error)
      }
    },
    [retryPodcastGeneration, mutate],
  )

  if (!focusedBookTab) {
    return <LibraryPodcastView />
  }

  if (selectedPodcast) {
    const bookTitle =
      focusedBookTab?.book.metadataTitle || focusedBookTab?.book.name
    return (
      <PodcastDetail
        podcast={selectedPodcast}
        bookTitle={bookTitle}
        onRetryPodcast={handleRetryPodcast}
        retryingPodcastId={retryingPodcastId}
      />
    )
  }

  return (
    <div className="space-y-4 p-4">
      {/* Current Book Info */}
      {podcasts.length === 0 ? (
        // No Podcasts
        <Card className="p-3">
          <div className="space-y-3">
            <div>
              <h3 className="text-foreground mb-1 text-sm font-medium leading-tight">
                {focusedBookTab.book.name}
              </h3>
              <p className="text-muted-foreground text-xs">
                {focusedBookTab.book.author ||
                  t('podcast.detail.author_unknown')}
              </p>
            </div>
            <Button
              onClick={handleCreatePodcast}
              disabled={
                isCreating || podcasts.some((p) => p.status === 'PROCESSING')
              }
              className="flex h-8 w-full items-center justify-center space-x-2"
              size="sm"
              aria-label={
                isCreating
                  ? t('podcast.pane.generating')
                  : t('podcast.pane.podcast_title', {
                      name: focusedBookTab.book.name,
                    })
              }
            >
              {isCreating ? (
                <>
                  <RefreshCw
                    className="h-3 w-3 animate-spin"
                    aria-hidden="true"
                  />
                  <span className="text-xs">
                    {t('podcast.pane.generating')}
                  </span>
                </>
              ) : (
                <span className="text-xs">
                  {t('podcast.pane.generate_podcast')}
                </span>
              )}
            </Button>
          </div>
        </Card>
      ) : (
        // Podcast List - 一覧表示を削除し、直接詳細画面に遷移
        <div>
          {error && (
            <Card className="mb-3 border-red-200 bg-red-50 p-3">
              <p className="text-xs text-red-700">
                {t('podcast.pane.loading_failed')}
              </p>
              <p className="mt-1 text-xs text-red-600">{error.message}</p>
              <Button
                variant="outline"
                size="sm"
                onClick={() => mutate()}
                className="mt-2 h-7 px-2 text-xs"
              >
                {t('podcast.list.retry')}
              </Button>
            </Card>
          )}

          {isLoading ? (
            <Card className="p-4">
              <div className="space-y-2 text-center">
                <RefreshCw className="text-primary mx-auto h-4 w-4 animate-spin" />
                <div>
                  <p className="text-foreground text-xs font-medium">
                    {t('podcast.pane.loading')}
                  </p>
                  <p className="text-muted-foreground text-xs">
                    {t('podcast.pane.fetching_info')}
                  </p>
                </div>
              </div>
            </Card>
          ) : (
            // ポッドキャストが存在する場合は自動的に詳細画面に遷移するため、
            // ここには到達しないはずだが、念のためローディング表示
            <Card className="p-4">
              <div className="space-y-2 text-center">
                <RefreshCw className="text-primary mx-auto h-4 w-4 animate-spin" />
                <div>
                  <p className="text-foreground text-xs font-medium">
                    {t('podcast.pane.loading')}
                  </p>
                  <p className="text-muted-foreground text-xs">
                    {t('podcast.pane.fetching_info')}
                  </p>
                </div>
              </div>
            </Card>
          )}
        </div>
      )}
    </div>
  )
}

export default PodcastPane
