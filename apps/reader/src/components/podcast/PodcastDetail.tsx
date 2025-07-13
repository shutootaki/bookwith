import {
  Download,
  MessageSquare,
  Share2,
  AlertCircle,
  RefreshCw,
} from 'lucide-react'
import React, { useState } from 'react'

import { usePodcastShare } from '../../hooks/podcast/usePodcastShare'
import { useTranslation } from '../../hooks/useTranslation'
import { reader } from '../../models'
import { PodcastResponse } from '../../types/podcast'
import { ResponsiveToolTip } from '../ResponsiveToolTip'
import { Button } from '../ui/button'
import { Card } from '../ui/card'

import { AudioPlayer } from './AudioPlayer'
import { PodcastScript } from './PodcastScript'

interface PodcastDetailProps {
  podcast: PodcastResponse
  bookTitle?: string
  className?: string
  onBack?: () => void
  onRetryPodcast?: (podcastId: string) => void
  retryingPodcastId?: string | null
}

export const PodcastDetail: React.FC<PodcastDetailProps> = ({
  podcast,
  bookTitle,
  onBack,
  onRetryPodcast,
  retryingPodcastId,
}) => {
  const t = useTranslation()
  const [showScript, setShowScript] = useState(false)
  const { handleDownload, handleShare } = usePodcastShare()

  const isFailed = podcast.status === 'FAILED'
  const isProcessing = podcast.status === 'PROCESSING'
  const isRetrying = retryingPodcastId === podcast.id

  const handleRetry = () => {
    if (onRetryPodcast) {
      onRetryPodcast(podcast.id)
    }
  }

  return (
    <div className="space-y-4 p-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        {onBack && (
          <Button variant="outline" size="sm" onClick={onBack} className="h-8">
            ← {t('podcast.detail.back')}
          </Button>
        )}
        <div className="flex items-center space-x-1">
          {podcast.script && !isFailed && !isProcessing && (
            <ResponsiveToolTip content={t('podcast.script')} align="center">
              <Button
                variant="outline"
                size="icon"
                onClick={() => setShowScript(!showScript)}
                className="h-8 w-8"
                aria-label={t('podcast.script')}
              >
                <MessageSquare className="h-3 w-3" />
              </Button>
            </ResponsiveToolTip>
          )}
          {podcast.audio_url && !isFailed && !isProcessing && (
            <>
              <Button
                variant="outline"
                size="icon"
                onClick={() =>
                  podcast.audio_url &&
                  handleDownload(podcast.audio_url, podcast.title)
                }
                className="h-8 w-8"
                aria-label={t('podcast.detail.download_short')}
              >
                <Download className="h-3 w-3" />
              </Button>
              <Button
                variant="outline"
                size="icon"
                onClick={() =>
                  podcast.audio_url &&
                  handleShare(podcast.audio_url, podcast.title)
                }
                className="h-8 w-8"
                aria-label={t('podcast.share')}
              >
                <Share2 className="h-3 w-3" />
              </Button>
            </>
          )}
        </div>
      </div>
      {/* Processing State */}
      {isProcessing && (
        <Card className="border-blue-200 bg-blue-50 p-6">
          <div className="flex flex-col items-center text-center">
            <RefreshCw className="mb-3 h-8 w-8 animate-spin text-blue-600" />
            <h3 className="mb-2 text-lg font-semibold text-blue-900">
              {t('podcast.status.processing')}
            </h3>
            <p className="text-muted-foreground text-sm">
              {t('podcast.book_item.generating_podcast_aria_label', {
                name: bookTitle,
              })}
            </p>
          </div>
        </Card>
      )}
      {/* Failed State */}
      {isFailed && !isProcessing && (
        <Card className="border-destructive/50 bg-destructive/5 p-6">
          <div className="flex flex-col items-center text-center">
            <AlertCircle className="text-destructive mb-3 h-8 w-8" />
            {bookTitle && (
              <p className="text-muted-foreground mb-1 text-sm">{bookTitle}</p>
            )}
            <h3 className="mb-2 text-lg font-semibold">
              {t('podcast.failed')}
            </h3>
            <p className="text-muted-foreground mb-4 text-sm">
              {t('podcast.failed_description')}
            </p>
            <Button
              variant="destructive"
              size="default"
              onClick={handleRetry}
              disabled={isRetrying || !onRetryPodcast}
            >
              {isRetrying ? (
                <>
                  <RefreshCw className="mr-2 h-4 w-4 animate-spin" />
                  {t('podcast.retrying')}
                </>
              ) : (
                <>
                  <RefreshCw className="mr-2 h-4 w-4" />
                  {t('podcast.retry')}
                </>
              )}
            </Button>
          </div>
        </Card>
      )}
      {/* Audio Player */}
      {podcast.audio_url && !isFailed && !isProcessing && (
        <Card className="px-4">
          <AudioPlayer
            audioUrl={podcast.audio_url}
            title={podcast.title}
            onPlay={() => {
              reader.setPodcast(podcast)
            }}
            onPause={() => {}}
            onEnd={() => {}}
          />
        </Card>
      )}
      {/* Script */}
      {showScript && podcast.script && !isFailed && !isProcessing && (
        <PodcastScript script={podcast.script} />
      )}
    </div>
  )
}
