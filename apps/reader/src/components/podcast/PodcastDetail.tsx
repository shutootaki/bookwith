import { motion } from 'framer-motion'
import { ArrowLeft, Download, MessageSquare, Share2 } from 'lucide-react'
import React, { useState } from 'react'

import { useTranslation } from '../../hooks/useTranslation'
import { reader, useReaderSnapshot } from '../../models'
import { PodcastResponse } from '../../types/podcast'
import {
  formatDate,
  isWebShareSupported,
  isClipboardSupported,
  generateAudioFilename,
  sanitizeErrorMessage,
} from '../../utils/podcast'
import { Button } from '../ui/button'
import { Card } from '../ui/card'
import { ScrollArea } from '../ui/scroll-area'

import { AudioPlayer } from './AudioPlayer'

interface PodcastDetailProps {
  podcast: PodcastResponse
  onBack: () => void
  className?: string
}

export const PodcastDetail: React.FC<PodcastDetailProps> = ({
  podcast,
  onBack,
  className = '',
}) => {
  const t = useTranslation()
  const [showScript, setShowScript] = useState(false)
  const { focusedBookTab } = useReaderSnapshot()

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
        // Fallback to copy to clipboard
        if (isClipboardSupported()) {
          navigator.clipboard.writeText(podcast.audio_url)
        }
      }
    } else if (isClipboardSupported()) {
      // Fallback to copy to clipboard
      navigator.clipboard.writeText(podcast.audio_url)
    }
  }

  // Get author from current book
  const author = focusedBookTab?.book?.author

  return (
    <div className={`space-y-4 ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <Button
          variant="ghost"
          size="sm"
          onClick={onBack}
          className="flex h-8 items-center space-x-1 px-2"
        >
          <ArrowLeft className="h-3 w-3" />
          <span className="text-xs">{t('podcast.detail.back')}</span>
        </Button>

        <div className="flex items-center space-x-1">
          {podcast.script && (
            <Button
              variant="outline"
              size="sm"
              onClick={() => setShowScript(!showScript)}
              className="flex h-7 items-center space-x-1 px-2"
            >
              <MessageSquare className="h-3 w-3" />
              <span className="text-xs">{t('podcast.script')}</span>
            </Button>
          )}

          {podcast.audio_url && (
            <>
              <Button
                variant="outline"
                size="sm"
                onClick={handleDownload}
                className="flex h-7 items-center space-x-1 px-2"
              >
                <Download className="h-3 w-3" />
                <span className="text-xs">
                  {t('podcast.detail.download_short')}
                </span>
              </Button>

              <Button
                variant="outline"
                size="sm"
                onClick={handleShare}
                className="flex h-7 items-center space-x-1 px-2"
              >
                <Share2 className="h-3 w-3" />
                <span className="text-xs">{t('podcast.share')}</span>
              </Button>
            </>
          )}
        </div>
      </div>

      {/* Audio Player */}
      {podcast.audio_url && (
        <Card className="p-4">
          <AudioPlayer
            audioUrl={podcast.audio_url}
            title={podcast.title}
            onPlay={() => {
              reader.setPodcast(podcast)
              console.log('Playing:', podcast.title)
            }}
            onPause={() => console.log('Paused:', podcast.title)}
            onEnd={() => console.log('Ended:', podcast.title)}
          />
        </Card>
      )}

      {/* Podcast Info */}
      <Card className="p-4">
        <div className="space-y-3">
          <div>
            <h2 className="text-foreground mb-2 text-lg font-semibold">
              {podcast.title}
            </h2>
            {author && <p className="text-foreground mb-2 text-sm">{author}</p>}
            <div className="text-muted-foreground space-y-1 text-xs">
              <p>
                {t('podcast.detail.created_at')}:{' '}
                {formatDate(podcast.created_at)}
              </p>
              <p>
                {t('podcast.detail.updated_at')}:{' '}
                {formatDate(podcast.updated_at)}
              </p>
              <p>
                {t('podcast.detail.status')}: {podcast.status}
              </p>
            </div>
          </div>

          {podcast.error_message && (
            <div className="rounded-md border border-red-200 bg-red-50 p-3">
              <p className="text-sm text-red-700">
                {t('podcast.detail.error')}:{' '}
                {sanitizeErrorMessage(podcast.error_message)}
              </p>
            </div>
          )}
        </div>
      </Card>

      {/* Script */}
      {showScript && podcast.script && (
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

export default PodcastDetail
