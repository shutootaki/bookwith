import { RefreshCw, Mic, Play, AlertCircle } from 'lucide-react'
import React, { memo } from 'react'

import { usePodcastsByBook } from '../../hooks/useSWR/usePodcast'
import { useTranslation } from '../../hooks/useTranslation'
import { components } from '../../lib/openapi-schema/schema'
import { PodcastResponse } from '../../types/podcast'
import { findPodcastByStatus } from '../../utils/podcast'
import { Button } from '../ui/button'
import { Card, CardContent } from '../ui/card'

interface BookPodcastItemProps {
  book: components['schemas']['BookDetail']
  podcasts?: PodcastResponse[]
  isCreating: boolean
  onCreatePodcast: () => void
  onPlayPodcast: (podcast: PodcastResponse) => void
  onPodcastsLoaded: (podcasts: PodcastResponse[]) => void
  onRetryPodcast?: (podcastId: string) => void
  retryingPodcastId?: string | null
}

export const BookPodcastItem = memo<BookPodcastItemProps>(
  ({
    book,
    podcasts: cachedPodcasts,
    isCreating,
    onCreatePodcast,
    onPlayPodcast,
    onPodcastsLoaded,
    onRetryPodcast,
    retryingPodcastId,
  }) => {
    const t = useTranslation()
    const { podcasts, isLoading, mutate } = usePodcastsByBook(book.id)

    React.useEffect(() => {
      if (podcasts.length > 0 && !cachedPodcasts) {
        onPodcastsLoaded(podcasts)
      }
    }, [podcasts, cachedPodcasts, onPodcastsLoaded])

    React.useEffect(() => {
      if (!isCreating) {
        mutate()
      }
    }, [isCreating, mutate])

    const displayPodcasts = cachedPodcasts || podcasts
    const completedPodcast = findPodcastByStatus(displayPodcasts, 'COMPLETED')
    const processingPodcast = findPodcastByStatus(displayPodcasts, 'PROCESSING')
    const failedPodcast = findPodcastByStatus(displayPodcasts, 'FAILED')
    const handleRetry = () => {
      if (failedPodcast && onRetryPodcast) {
        // 楽観的更新：ローカルで状態をPROCESSINGに変更
        const optimisticPodcasts = displayPodcasts.map((podcast) =>
          podcast.id === failedPodcast.id
            ? { ...podcast, status: 'PROCESSING' as const }
            : podcast,
        )
        onPodcastsLoaded(optimisticPodcasts)
        onRetryPodcast(failedPodcast.id)
      }
    }
    const isRetrying = retryingPodcastId === failedPodcast?.id
    const bookTitle = book.metadataTitle || book.name

    // ローディング状態の表示
    const renderLoadingState = () => (
      <div className="flex items-center justify-center p-2">
        <RefreshCw className="text-muted-foreground h-4 w-4 animate-spin" />
      </div>
    )

    // 完了状態のポッドキャストボタン
    const renderCompletedPodcastButton = () => (
      <Button
        size="sm"
        variant="default"
        onClick={() => onPlayPodcast(completedPodcast!)}
        className="w-full"
        aria-label={t('podcast.book_item.play_podcast_aria_label', {
          name: bookTitle,
        })}
      >
        <Play className="mr-1 h-3 w-3" aria-hidden="true" />
        <span className="text-xs">{t('podcast.play')}</span>
      </Button>
    )

    // 処理中状態のポッドキャストボタン
    const renderProcessingPodcastButton = () => (
      <Button
        size="sm"
        variant="outline"
        disabled
        className="w-full"
        aria-label={t('podcast.book_item.generating_podcast_aria_label', {
          name: bookTitle,
        })}
      >
        <RefreshCw className="mr-1 h-3 w-3 animate-spin" aria-hidden="true" />
        <span className="text-xs">{t('podcast.pane.generating')}</span>
      </Button>
    )

    // 失敗状態のポッドキャスト表示
    const renderFailedPodcastContent = () => (
      <div className="w-full space-y-2">
        <div className="flex text-red-600">
          <AlertCircle className="mr-1 h-3 w-3" />
          <span className="text-xs">{t('podcast.failed')}</span>
        </div>
        {onRetryPodcast && (
          <Button
            size="sm"
            variant="outline"
            onClick={handleRetry}
            disabled={isRetrying}
            className="w-full"
            aria-label={t('podcast.retry')}
          >
            {isRetrying ? (
              <>
                <RefreshCw
                  className="mr-1 h-3 w-3 animate-spin"
                  aria-hidden="true"
                />
                <span className="text-xs">{t('podcast.retrying')}</span>
              </>
            ) : (
              <>
                <RefreshCw className="mr-1 h-3 w-3" aria-hidden="true" />
                <span className="text-xs">{t('podcast.retry')}</span>
              </>
            )}
          </Button>
        )}
      </div>
    )

    const renderCreatePodcastButton = () => {
      const ariaLabel = isCreating
        ? t('podcast.book_item.generating_podcast_aria_label', {
            name: bookTitle,
          })
        : t('podcast.book_item.generate_podcast_aria_label', {
            name: bookTitle,
          })

      return (
        <Button
          size="sm"
          variant="outline"
          onClick={onCreatePodcast}
          disabled={isCreating}
          className="w-full"
          aria-label={ariaLabel}
        >
          {isCreating ? (
            <>
              <RefreshCw
                className="mr-1 h-3 w-3 animate-spin"
                aria-hidden="true"
              />
              <span className="text-xs">{t('podcast.pane.generating')}</span>
            </>
          ) : (
            <>
              <Mic className="mr-1 h-3 w-3" aria-hidden="true" />
              <span className="text-xs">{t('podcast.generate')}</span>
            </>
          )}
        </Button>
      )
    }

    // メインの表示ロジック
    const renderMainContent = () => {
      if (completedPodcast) {
        return renderCompletedPodcastButton()
      }
      if (processingPodcast) {
        return renderProcessingPodcastButton()
      }
      if (failedPodcast) {
        return renderFailedPodcastContent()
      }
      return renderCreatePodcastButton()
    }

    return (
      <Card className="h-full transition-all hover:shadow-md">
        <CardContent className="p-3">
          <div className="flex h-full flex-col justify-between">
            <div className="flex-1">
              <h4 className="text-foreground truncate text-sm font-medium leading-tight">
                {bookTitle}
              </h4>
              {book.author && (
                <p className="text-muted-foreground mb-3 truncate text-xs">
                  {book.author}
                </p>
              )}
            </div>
            <div className="flex justify-center">
              {isLoading ? renderLoadingState() : renderMainContent()}
            </div>
          </div>
        </CardContent>
      </Card>
    )
  },
)
