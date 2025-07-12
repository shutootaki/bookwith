import { RefreshCw, Mic, Play, AlertCircle } from 'lucide-react'
import React, { memo } from 'react'

import { usePodcastsByBook } from '../../hooks/useSWR/usePodcast'
import { useTranslation } from '../../hooks/useTranslation'
import { components } from '../../lib/openapi-schema/schema'
import { PodcastResponse } from '../../types/podcast'
import {
  getCompletedPodcast,
  getProcessingPodcast,
  getFailedPodcast,
} from '../../utils/podcast'
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
    const { podcasts, isLoading } = usePodcastsByBook(book.id)

    // ポッドキャストがロードされたらキャッシュに保存
    React.useEffect(() => {
      if (podcasts.length > 0 && !cachedPodcasts) {
        onPodcastsLoaded(podcasts)
      }
    }, [podcasts, cachedPodcasts, onPodcastsLoaded])

    const displayPodcasts = cachedPodcasts || podcasts
    const completedPodcast = getCompletedPodcast(displayPodcasts)
    const processingPodcast = getProcessingPodcast(displayPodcasts)
    const failedPodcast = getFailedPodcast(displayPodcasts)
    const handleRetry = () => {
      if (failedPodcast && onRetryPodcast) {
        onRetryPodcast(failedPodcast.id)
      }
    }
    const isRetrying = retryingPodcastId === failedPodcast?.id
    const bookTitle = book.metadataTitle || book.name

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
              {isLoading ? (
                <div className="flex items-center justify-center p-2">
                  <RefreshCw className="text-muted-foreground h-4 w-4 animate-spin" />
                </div>
              ) : (
                <>
                  {completedPodcast ? (
                    <Button
                      size="sm"
                      variant="default"
                      onClick={() => onPlayPodcast(completedPodcast)}
                      className="w-full"
                      aria-label={t(
                        'podcast.book_item.play_podcast_aria_label',
                        {
                          name: bookTitle,
                        },
                      )}
                    >
                      <Play className="mr-1 h-3 w-3" aria-hidden="true" />
                      <span className="text-xs">{t('podcast.play')}</span>
                    </Button>
                  ) : processingPodcast ? (
                    <Button
                      size="sm"
                      variant="outline"
                      disabled
                      className="w-full"
                      aria-label={t(
                        'podcast.book_item.generating_podcast_aria_label',
                        {
                          name: bookTitle,
                        },
                      )}
                    >
                      <RefreshCw
                        className="mr-1 h-3 w-3 animate-spin"
                        aria-hidden="true"
                      />
                      <span className="text-xs">
                        {t('podcast.pane.generating')}
                      </span>
                    </Button>
                  ) : failedPodcast ? (
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
                              <span className="text-xs">
                                {t('podcast.retrying')}
                              </span>
                            </>
                          ) : (
                            <>
                              <RefreshCw
                                className="mr-1 h-3 w-3"
                                aria-hidden="true"
                              />
                              <span className="text-xs">
                                {t('podcast.retry')}
                              </span>
                            </>
                          )}
                        </Button>
                      )}
                    </div>
                  ) : (
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={onCreatePodcast}
                      disabled={isCreating}
                      className="w-full"
                      aria-label={
                        isCreating
                          ? t(
                              'podcast.book_item.generating_podcast_aria_label',
                              {
                                name: bookTitle,
                              },
                            )
                          : t('podcast.book_item.generate_podcast_aria_label', {
                              name: bookTitle,
                            })
                      }
                    >
                      {isCreating ? (
                        <>
                          <RefreshCw
                            className="mr-1 h-3 w-3 animate-spin"
                            aria-hidden="true"
                          />
                          <span className="text-xs">
                            {t('podcast.pane.generating')}
                          </span>
                        </>
                      ) : (
                        <>
                          <Mic className="mr-1 h-3 w-3" aria-hidden="true" />
                          <span className="text-xs">
                            {t('podcast.generate')}
                          </span>
                        </>
                      )}
                    </Button>
                  )}
                </>
              )}
            </div>
          </div>
        </CardContent>
      </Card>
    )
  },
)

BookPodcastItem.displayName = 'BookPodcastItem'
