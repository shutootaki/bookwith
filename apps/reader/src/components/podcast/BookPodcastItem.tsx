import { RefreshCw, Mic, Play } from 'lucide-react'
import React from 'react'

import { usePodcastsByBook } from '../../hooks/useSWR/usePodcast'
import { useTranslation } from '../../hooks/useTranslation'
import { components } from '../../lib/openapi-schema/schema'
import { PodcastResponse } from '../../types/podcast'
import { getCompletedPodcast, getProcessingPodcast } from '../../utils/podcast'
import { StateLayer } from '../StateLayer'
import { Button } from '../ui/button'
import { Card } from '../ui/card'

interface BookPodcastItemProps {
  book: components['schemas']['BookDetail']
  podcasts?: PodcastResponse[]
  isCreating: boolean
  onCreatePodcast: () => void
  onPlayPodcast: (podcast: PodcastResponse) => void
  onOpenBook: () => void
  onPodcastsLoaded: (podcasts: PodcastResponse[]) => void
}

export const BookPodcastItem: React.FC<BookPodcastItemProps> = ({
  book,
  podcasts: cachedPodcasts,
  isCreating,
  onCreatePodcast,
  onPlayPodcast,
  onOpenBook,
  onPodcastsLoaded,
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

  return (
    <Card className="p-3">
      <div className="flex items-start justify-between">
        <button
          className="relative flex-1 text-left"
          onClick={onOpenBook}
          aria-label={`${book.name}を開く${
            book.author ? ` (著者: ${book.author})` : ''
          }`}
        >
          <StateLayer />
          <h4 className="text-foreground truncate text-sm font-medium leading-tight">
            {book.name}
          </h4>
          {book.author && (
            <p className="text-muted-foreground truncate text-xs">
              {book.author}
            </p>
          )}
        </button>

        <div className="ml-2 flex items-center gap-1">
          {isLoading ? (
            <RefreshCw className="text-muted-foreground h-3 w-3 animate-spin" />
          ) : (
            <>
              {completedPodcast ? (
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => onPlayPodcast(completedPodcast)}
                  className="flex h-7 items-center gap-1 px-2"
                  aria-label={`${book.name}のポッドキャストを再生`}
                >
                  <Play className="h-3 w-3" aria-hidden="true" />
                  <span className="text-xs">{t('podcast.play')}</span>
                </Button>
              ) : processingPodcast ? (
                <Button
                  size="sm"
                  variant="outline"
                  disabled
                  className="flex h-7 items-center gap-1 px-2"
                  aria-label={`${book.name}のポッドキャスト生成中`}
                >
                  <RefreshCw
                    className="h-3 w-3 animate-spin"
                    aria-hidden="true"
                  />
                  <span className="text-xs">
                    {t('podcast.pane.generating')}
                  </span>
                </Button>
              ) : (
                <Button
                  size="sm"
                  variant="outline"
                  onClick={onCreatePodcast}
                  disabled={isCreating}
                  className="flex h-7 items-center gap-1 px-2"
                  aria-label={
                    isCreating
                      ? `${book.name}のポッドキャスト生成中`
                      : `${book.name}のポッドキャストを生成`
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
                    <>
                      <Mic className="h-3 w-3" aria-hidden="true" />
                      <span className="text-xs">{t('podcast.generate')}</span>
                    </>
                  )}
                </Button>
              )}
            </>
          )}
        </div>
      </div>
    </Card>
  )
}
