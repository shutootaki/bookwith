import React, { useCallback, useState } from 'react'

import { useLibrary, usePodcastActions } from '../../hooks'
import { useTranslation } from '../../hooks/useTranslation'
import { reader } from '../../models'
import { PodcastResponse } from '../../types/podcast'
import { lock } from '../../utils/styles'

import { BookPodcastItem } from './BookPodcastItem'
import { PodcastDetail } from './PodcastDetail'

export const LibraryPodcastView: React.FC = () => {
  const t = useTranslation()
  const { books } = useLibrary()
  const { createPodcast, retryPodcastGeneration, retryingPodcastId } =
    usePodcastActions()
  const [selectedBookId, setSelectedBookId] = useState<string | null>(null)
  const [creatingBookId, setCreatingBookId] = useState<string | null>(null)
  const [podcastsMap, setPodcastsMap] = useState<{
    [bookId: string]: PodcastResponse[]
  }>({})

  const handleCreatePodcast = useCallback(
    async (bookId: string, bookName: string) => {
      setCreatingBookId(bookId)
      try {
        await createPodcast(bookId, bookName)
      } catch (error) {
        console.error('Failed to create podcast:', error)
      } finally {
        setCreatingBookId(null)
      }
    },
    [createPodcast],
  )

  const handlePlayPodcast = useCallback(
    (podcast: PodcastResponse, bookId: string) => {
      reader.setPodcast(podcast)
      setSelectedBookId(bookId)
    },
    [],
  )

  const handlePodcastsLoaded = useCallback(
    (bookId: string, podcasts: PodcastResponse[]) => {
      setPodcastsMap((prev) => ({
        ...prev,
        [bookId]: podcasts,
      }))
    },
    [],
  )

  const handleRetryPodcast = useCallback(
    async (podcastId: string) => {
      try {
        await retryPodcastGeneration(podcastId)
      } catch (error) {
        console.error('Failed to retry podcast:', error)
      }
    },
    [retryPodcastGeneration],
  )

  // 選択された本のポッドキャストを表示
  if (selectedBookId) {
    const podcasts = podcastsMap[selectedBookId] || []
    const selectedPodcast = podcasts.find(
      (p) => p.status === 'COMPLETED' || p.status === 'FAILED',
    )
    const selectedBook = books.find((b) => b.id === selectedBookId)

    if (selectedPodcast) {
      return (
        <PodcastDetail
          podcast={selectedPodcast}
          book={selectedBook!}
          onBack={() => setSelectedBookId(null)}
        />
      )
    }
  }

  if (books.length === 0) {
    return (
      <div className="flex h-full items-center justify-center px-4">
        <p className="text-muted-foreground">{t('podcast.list.empty')}</p>
      </div>
    )
  }

  return (
    <div className="flex h-full flex-col px-4">
      <div className="mb-4 flex-shrink-0">
        <p className="text-muted-foreground mt-1 text-xs">
          {t('podcast.library.description')}
        </p>
      </div>

      <div className="flex-1 overflow-y-auto">
        <ul
          className="grid"
          style={{
            gridTemplateColumns: `repeat(auto-fill, minmax(calc(120px + 2vw), 1fr))`,
            columnGap: lock(12, 24),
            rowGap: lock(16, 24),
          }}
        >
          {books.map((book) => (
            <li key={book.id}>
              <BookPodcastItem
                book={book}
                podcasts={podcastsMap[book.id]}
                isCreating={creatingBookId === book.id}
                onCreatePodcast={() =>
                  handleCreatePodcast(book.id, book.metadataTitle || book.name)
                }
                onPlayPodcast={(podcast: PodcastResponse) =>
                  handlePlayPodcast(podcast, book.id)
                }
                onPodcastsLoaded={(podcasts: PodcastResponse[]) =>
                  handlePodcastsLoaded(book.id, podcasts)
                }
                onRetryPodcast={handleRetryPodcast}
                retryingPodcastId={retryingPodcastId}
              />
            </li>
          ))}
        </ul>
      </div>
    </div>
  )
}
