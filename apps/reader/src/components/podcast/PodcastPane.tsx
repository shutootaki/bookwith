import { Mic, Play, RefreshCw } from 'lucide-react'
import React, { useState } from 'react'
import { toast } from 'sonner'

import { useLibrary } from '../../hooks'
import { usePodcastsByBook } from '../../hooks/useSWR/usePodcast'
import { useTranslation } from '../../hooks/useTranslation'
import {
  createPodcast,
  retryPodcast,
} from '../../lib/apiHandler/podcastApiHandler'
import { components } from '../../lib/openapi-schema/schema'
import { reader, useReaderSnapshot } from '../../models'
import { PodcastResponse } from '../../types/podcast'
import { generatePodcastTitle, isPodcastProcessing } from '../../utils/podcast'
import { StateLayer } from '../StateLayer'
import { Button } from '../ui/button'
import { Card } from '../ui/card'

// import { LibraryPodcastView } from './LibraryPodcastView'
import { PodcastDetail } from './PodcastDetail'
import { PodcastList } from './PodcastList'

interface PodcastPaneProps {
  className?: string
}

export const PodcastPane: React.FC<PodcastPaneProps> = ({ className = '' }) => {
  const t = useTranslation()
  const { focusedBookTab } = useReaderSnapshot()
  const [selectedPodcast, setSelectedPodcast] =
    useState<PodcastResponse | null>(null)
  const [isCreating, setIsCreating] = useState(false)
  const [retryingPodcastId, setRetryingPodcastId] = useState<string | null>(
    null,
  )

  const { podcasts, isLoading, error, mutate } = usePodcastsByBook(
    focusedBookTab?.book.id,
  )

  const handleCreatePodcast = async () => {
    if (!focusedBookTab?.book.id) return

    setIsCreating(true)
    try {
      const result = await createPodcast(
        focusedBookTab.book.id,
        generatePodcastTitle(focusedBookTab.book.name),
      )

      if (result) {
        toast.success(t('podcast.pane.generation_started'))
        mutate() // Refresh the podcast list
      } else {
        toast.error(t('podcast.pane.generation_failed'))
      }
    } catch (error) {
      console.error('Error creating podcast:', error)
      toast.error(t('podcast.pane.generation_failed'))
    } finally {
      setIsCreating(false)
    }
  }

  const handlePlayPodcast = (podcast: PodcastResponse) => {
    reader.setPodcast(podcast)
    setSelectedPodcast(podcast)
  }

  const handleRetryPodcast = async (podcastId: string) => {
    setRetryingPodcastId(podcastId)
    try {
      const result = await retryPodcast(podcastId)

      if (result) {
        toast.success(t('podcast.pane.regeneration_started'))
        mutate() // Refresh the podcast list
      } else {
        toast.error(t('podcast.pane.regeneration_failed'))
      }
    } catch (error) {
      console.error('Error retrying podcast:', error)
      toast.error(t('podcast.pane.regeneration_failed'))
    } finally {
      setRetryingPodcastId(null)
    }
  }

  if (!focusedBookTab) {
    return <LibraryPodcastView className={className} />
  }

  if (selectedPodcast) {
    return (
      <PodcastDetail
        podcast={selectedPodcast}
        onBack={() => setSelectedPodcast(null)}
        className={className}
      />
    )
  }

  return (
    <div className={`space-y-4 ${className}`}>
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
                isCreating ||
                podcasts.some((p) => isPodcastProcessing(p.status))
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
        // Podcast List
        <div>
          <div className="mb-3 flex items-center justify-between">
            <h3 className="text-foreground text-sm font-medium">
              {t('podcast.pane.podcast_list')}
            </h3>
            <Button
              variant="outline"
              size="sm"
              onClick={() => mutate()}
              disabled={isLoading}
              className="flex h-7 items-center space-x-1 px-2"
              aria-label={
                isLoading
                  ? 'ポッドキャスト一覧を更新中'
                  : 'ポッドキャスト一覧を更新'
              }
            >
              <RefreshCw
                className={`h-3 w-3 ${isLoading ? 'animate-spin' : ''}`}
                aria-hidden="true"
              />
              <span className="text-xs">{t('podcast.refresh')}</span>
            </Button>
          </div>

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
            <PodcastList
              podcasts={podcasts}
              onPlay={handlePlayPodcast}
              onRetry={handleRetryPodcast}
              retryingPodcastId={retryingPodcastId}
            />
          )}
        </div>
      )}
    </div>
  )
}

interface LibraryPodcastViewProps {
  className?: string
}

const LibraryPodcastView: React.FC<LibraryPodcastViewProps> = ({
  className = '',
}) => {
  const { books } = useLibrary()
  const [selectedBookId, setSelectedBookId] = useState<string | null>(null)
  const [creatingBookId, setCreatingBookId] = useState<string | null>(null)
  const [podcastsMap, setPodcastsMap] = useState<{
    [bookId: string]: PodcastResponse[]
  }>({})

  // 選択された本のポッドキャストを表示
  if (selectedBookId) {
    const podcasts = podcastsMap[selectedBookId] || []
    const selectedPodcast = podcasts.find((p) => p.status === 'COMPLETED')

    if (selectedPodcast) {
      return (
        <PodcastDetail
          podcast={selectedPodcast}
          onBack={() => setSelectedBookId(null)}
          className={className}
        />
      )
    }
  }

  const handleCreatePodcast = async (bookId: string, bookName: string) => {
    setCreatingBookId(bookId)
    try {
      const result = await createPodcast(bookId, `${bookName}のポッドキャスト`)

      if (result) {
        toast.success('ポッドキャストの生成を開始しました')
        // 作成されたポッドキャストのIDを使って詳細を取得することもできるが、
        // ここでは生成中のステータスだけを追跡
        // 実際のポッドキャストデータはusePodcastsByBookフックが自動的に更新する
      } else {
        toast.error('ポッドキャストの生成に失敗しました')
      }
    } catch (error) {
      console.error('Error creating podcast:', error)
      toast.error('ポッドキャストの生成に失敗しました')
    } finally {
      setCreatingBookId(null)
    }
  }

  return (
    <div className={`space-y-3 ${className}`}>
      <div className="mb-3">
        <h3 className="text-foreground text-sm font-medium">ライブラリ</h3>
        <p className="text-muted-foreground mt-1 text-xs">
          本を選択してポッドキャストを生成・再生できます
        </p>
      </div>

      {books.map((book) => (
        <BookPodcastItem
          key={book.id}
          book={book}
          podcasts={podcastsMap[book.id]}
          isCreating={creatingBookId === book.id}
          onCreatePodcast={() => handleCreatePodcast(book.id, book.name)}
          onPlayPodcast={(podcast) => {
            reader.setPodcast(podcast)
            setSelectedBookId(book.id)
          }}
          onOpenBook={() => reader.addTab(book)}
          onPodcastsLoaded={(podcasts) => {
            setPodcastsMap((prev) => ({
              ...prev,
              [book.id]: podcasts,
            }))
          }}
        />
      ))}
    </div>
  )
}

interface BookPodcastItemProps {
  book: components['schemas']['BookDetail']
  podcasts?: PodcastResponse[]
  isCreating: boolean
  onCreatePodcast: () => void
  onPlayPodcast: (podcast: PodcastResponse) => void
  onOpenBook: () => void
  onPodcastsLoaded: (podcasts: PodcastResponse[]) => void
}

const BookPodcastItem: React.FC<BookPodcastItemProps> = ({
  book,
  podcasts: cachedPodcasts,
  isCreating,
  onCreatePodcast,
  onPlayPodcast,
  onOpenBook,
  onPodcastsLoaded,
}) => {
  const { podcasts, isLoading } = usePodcastsByBook(book.id)

  // ポッドキャストがロードされたらキャッシュに保存
  React.useEffect(() => {
    if (podcasts.length > 0 && !cachedPodcasts) {
      onPodcastsLoaded(podcasts)
    }
  }, [podcasts, cachedPodcasts, onPodcastsLoaded])

  const displayPodcasts = cachedPodcasts || podcasts
  const completedPodcast = displayPodcasts.find((p) => p.status === 'COMPLETED')
  const processingPodcast = displayPodcasts.find(
    (p) => p.status === 'PROCESSING',
  )

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
                  <span className="text-xs">再生</span>
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
                  <span className="text-xs">生成中</span>
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
                      <span className="text-xs">生成中</span>
                    </>
                  ) : (
                    <>
                      <Mic className="h-3 w-3" aria-hidden="true" />
                      <span className="text-xs">生成</span>
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

export default PodcastPane
