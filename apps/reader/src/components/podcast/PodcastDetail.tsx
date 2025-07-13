import { Download, MessageSquare, Share2 } from 'lucide-react'
import React, { useState, memo } from 'react'

import { PODCAST_ICON_SIZES, PODCAST_UI_CLASSES } from '../../constants/podcast'
import { usePodcastActions } from '../../hooks/podcast/usePodcastActions'
import { usePodcastShare } from '../../hooks/podcast/usePodcastShare'
import { useTranslation } from '../../hooks/useTranslation'
import { components } from '../../lib/openapi-schema/schema'
import { reader } from '../../models'
import { PodcastResponse } from '../../types/podcast'
import { Button } from '../ui/button'
import { Card } from '../ui/card'

import { AudioPlayer } from './AudioPlayer'
import { BookPodcastItem } from './BookPodcastItem'
import { PodcastScript } from './PodcastScript'

export interface PodcastDetailProps {
  podcast?: PodcastResponse
  book: components['schemas']['BookDetail']
  className?: string
  onBack?: () => void
}

export const PodcastDetail: React.FC<PodcastDetailProps> = memo(
  ({ podcast, book, onBack }) => {
    const t = useTranslation()
    const [showScript, setShowScript] = useState(false)
    const [currentTime, setCurrentTime] = useState(0)
    const { handleDownload, handleShare } = usePodcastShare()
    const {
      isCreating,
      createPodcast,
      retryPodcastGeneration,
      retryingPodcastId,
    } = usePodcastActions()

    // ポッドキャストが存在しない場合
    if (!podcast) {
      return (
        <div className="flex flex-col">
          <div className="flex-1 space-y-4 overflow-y-auto p-4">
            <div className="flex items-center justify-between">
              {onBack && (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={onBack}
                  className="h-8"
                >
                  ← {t('podcast.detail.back')}
                </Button>
              )}
            </div>
            <BookPodcastItem
              book={book}
              isCreating={isCreating}
              onCreatePodcast={async () => {
                if (!book) return
                await createPodcast(book.id, book.name)
              }}
              onPlayPodcast={() => {}}
              onPodcastsLoaded={() => {}}
              onRetryPodcast={retryPodcastGeneration}
              retryingPodcastId={retryingPodcastId}
            />
          </div>
        </div>
      )
    }

    // ポッドキャストが完了していない場合はBookPodcastItemを使用
    if (podcast.status !== 'COMPLETED') {
      return (
        <div className="flex flex-col">
          <div className="flex-1 space-y-4 overflow-y-auto p-4">
            <div className="flex items-center justify-between">
              {onBack && (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={onBack}
                  className="h-8"
                >
                  ← {t('podcast.detail.back')}
                </Button>
              )}
            </div>
            <BookPodcastItem
              book={book}
              podcasts={[podcast]}
              isCreating={isCreating}
              onCreatePodcast={async () => {
                if (!book) return
                await createPodcast(book.id, book.name)
              }}
              onPlayPodcast={() => {}}
              onPodcastsLoaded={() => {}}
              onRetryPodcast={retryPodcastGeneration}
              retryingPodcastId={retryingPodcastId}
            />
          </div>
        </div>
      )
    }

    // ポッドキャストが完了している場合は詳細UIを表示
    return (
      <div className="flex h-full flex-col overflow-hidden">
        <div className="space-y-4 overflow-y-auto px-4">
          <div className="flex items-center justify-between">
            {onBack && (
              <Button
                variant="outline"
                size="sm"
                onClick={onBack}
                className="h-8"
              >
                ← {t('podcast.detail.back')}
              </Button>
            )}
            <div className="flex items-center space-x-1">
              {podcast.script && (
                <Button
                  variant="outline"
                  size="icon"
                  onClick={() => setShowScript(!showScript)}
                  className={PODCAST_UI_CLASSES.CONTROL_BUTTON}
                  aria-label={t('podcast.script')}
                >
                  <MessageSquare className={PODCAST_ICON_SIZES.XS} />
                </Button>
              )}
              {podcast.audio_url && (
                <>
                  <Button
                    variant="outline"
                    size="icon"
                    onClick={() =>
                      podcast.audio_url &&
                      handleDownload(podcast.audio_url, podcast.title)
                    }
                    className={PODCAST_UI_CLASSES.CONTROL_BUTTON}
                    aria-label={t('podcast.detail.download_short')}
                  >
                    <Download className={PODCAST_ICON_SIZES.XS} />
                  </Button>
                  <Button
                    variant="outline"
                    size="icon"
                    onClick={() =>
                      podcast.audio_url &&
                      handleShare(podcast.audio_url, podcast.title)
                    }
                    className={PODCAST_UI_CLASSES.CONTROL_BUTTON}
                    aria-label={t('podcast.share')}
                  >
                    <Share2 className={PODCAST_ICON_SIZES.XS} />
                  </Button>
                </>
              )}
            </div>
          </div>
          {podcast.audio_url && (
            <Card className="px-4">
              <AudioPlayer
                audioUrl={podcast.audio_url}
                title={podcast.title}
                onPlay={() => {
                  reader.setPodcast(podcast)
                }}
                onPause={() => {}}
                onEnd={() => {}}
                onTimeUpdate={setCurrentTime}
                onSeek={(time) => {
                  if (window.podcastSeekFunction) {
                    window.podcastSeekFunction(time)
                  }
                }}
              />
            </Card>
          )}
          {showScript && podcast.script && (
            <PodcastScript
              script={podcast.script}
              currentTime={currentTime}
              onTimeSeek={(time) => {
                if (window.podcastSeekFunction) {
                  window.podcastSeekFunction(time)
                }
              }}
            />
          )}
        </div>
      </div>
    )
  },
)
