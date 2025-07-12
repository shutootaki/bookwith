import { motion } from 'framer-motion'
import {
  Download,
  MessageSquare,
  Share2,
  AlertCircle,
  RefreshCw,
} from 'lucide-react'
import React, { useState } from 'react'

import { useTranslation } from '../../hooks/useTranslation'
import { reader } from '../../models'
import { PodcastResponse } from '../../types/podcast'
import {
  isWebShareSupported,
  isClipboardSupported,
  generateAudioFilename,
  isPodcastFailed,
  isPodcastProcessing, // 追加
} from '../../utils/podcast'
import { Button } from '../ui/button'
import { Card } from '../ui/card'
import { ScrollArea } from '../ui/scroll-area'

import { AudioPlayer } from './AudioPlayer'

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

  const isFailed = isPodcastFailed(podcast.status)
  const isProcessing = isPodcastProcessing(podcast.status) // 追加
  const isRetrying = retryingPodcastId === podcast.id

  const handleDownload = async () => {
    if (!podcast.audio_url) return
    try {
      const response = await fetch(podcast.audio_url)
      const blob = await response.blob()
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = generateAudioFilename(podcast.title)
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      URL.revokeObjectURL(url)
    } catch (error) {
      console.error('Download failed:', error)
    }
  }

  const handleShare = async () => {
    if (!podcast.audio_url) return
    if (isWebShareSupported()) {
      try {
        await navigator.share({
          title: podcast.title,
          text: t('podcast.pane.podcast_title', { name: podcast.title }),
          url: podcast.audio_url,
        })
      } catch {
        if (isClipboardSupported()) {
          navigator.clipboard.writeText(podcast.audio_url)
        }
      }
    } else if (isClipboardSupported()) {
      navigator.clipboard.writeText(podcast.audio_url)
    }
  }

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
            <Button
              variant="outline"
              size="icon"
              onClick={() => setShowScript(!showScript)}
              className="h-8 w-8"
              aria-label={t('podcast.script')}
            >
              <MessageSquare className="h-3 w-3" />
            </Button>
          )}
          {podcast.audio_url && !isFailed && !isProcessing && (
            <>
              <Button
                variant="outline"
                size="icon"
                onClick={handleDownload}
                className="h-8 w-8"
                aria-label={t('podcast.detail.download_short')}
              >
                <Download className="h-3 w-3" />
              </Button>
              <Button
                variant="outline"
                size="icon"
                onClick={handleShare}
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
        <motion.div
          initial={{ opacity: 0, height: 0 }}
          animate={{ opacity: 1, height: 'auto' }}
          exit={{ opacity: 0, height: 0 }}
          transition={{ duration: 0.3 }}
        >
          <Card className="p-6">
            <h3 className="text-foreground mb-4 text-lg font-semibold">
              {t('podcast.script')}
            </h3>
            <ScrollArea className="h-96">
              <div className="space-y-4">
                {podcast.script.map((turn, index) => (
                  <div key={index} className="flex space-x-3">
                    <div className="flex-shrink-0">
                      <span className="bg-primary text-primary-foreground inline-flex h-8 w-8 items-center justify-center rounded-full text-sm font-medium">
                        {turn.speaker}
                      </span>
                    </div>
                    <div className="flex-1">
                      <p className="text-foreground text-sm leading-relaxed">
                        {turn.text}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            </ScrollArea>
          </Card>
        </motion.div>
      )}
    </div>
  )
}
