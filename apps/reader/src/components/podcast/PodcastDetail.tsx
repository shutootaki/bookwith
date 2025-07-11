import { motion } from 'framer-motion'
import { ArrowLeft, Download, MessageSquare, Share2 } from 'lucide-react'
import React, { useState } from 'react'

import { components } from '../../lib/openapi-schema/schema'
import { reader } from '../../models'
import { Button } from '../ui/button'
import { Card } from '../ui/card'
import { ScrollArea } from '../ui/scroll-area'

import { AudioPlayer } from './AudioPlayer'

type PodcastResponse = components['schemas']['PodcastResponse']

interface PodcastDetailProps {
  podcast: PodcastResponse
  onBack: () => void
  onDownload?: (audioUrl: string, title: string) => void
  onShare?: (podcast: PodcastResponse) => void
  className?: string
}

export const PodcastDetail: React.FC<PodcastDetailProps> = ({
  podcast,
  onBack,
  onDownload,
  onShare,
  className = '',
}) => {
  const [showScript, setShowScript] = useState(false)

  const handleDownload = async () => {
    if (!podcast.audio_url) return
    
    try {
      const response = await fetch(podcast.audio_url)
      const blob = await response.blob()
      const url = URL.createObjectURL(blob)
      
      const a = document.createElement('a')
      a.href = url
      a.download = `${podcast.title}.mp3`
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      URL.revokeObjectURL(url)
    } catch (error) {
      console.error('Download failed:', error)
    }
  }

  const handleShare = async () => {
    if (navigator.share && podcast.audio_url) {
      try {
        await navigator.share({
          title: podcast.title,
          text: `ポッドキャスト: ${podcast.title}`,
          url: podcast.audio_url,
        })
      } catch (error) {
        // Fallback to copy to clipboard
        navigator.clipboard.writeText(podcast.audio_url)
      }
    } else if (podcast.audio_url) {
      // Fallback to copy to clipboard
      navigator.clipboard.writeText(podcast.audio_url)
    }
  }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString('ja-JP')
  }

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <Button
          variant="ghost"
          size="sm"
          onClick={onBack}
          className="flex items-center space-x-1"
        >
          <ArrowLeft className="h-4 w-4" />
          <span>戻る</span>
        </Button>

        <div className="flex items-center space-x-2">
          {podcast.script && (
            <Button
              variant="outline"
              size="sm"
              onClick={() => setShowScript(!showScript)}
              className="flex items-center space-x-1"
            >
              <MessageSquare className="h-4 w-4" />
              <span>台本</span>
            </Button>
          )}
          
          {podcast.audio_url && (
            <>
              <Button
                variant="outline"
                size="sm"
                onClick={handleDownload}
                className="flex items-center space-x-1"
              >
                <Download className="h-4 w-4" />
                <span>ダウンロード</span>
              </Button>
              
              <Button
                variant="outline"
                size="sm"
                onClick={handleShare}
                className="flex items-center space-x-1"
              >
                <Share2 className="h-4 w-4" />
                <span>共有</span>
              </Button>
            </>
          )}
        </div>
      </div>

      {/* Audio Player */}
      {podcast.audio_url && (
        <Card className="p-6">
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
      <Card className="p-6">
        <div className="space-y-4">
          <div>
            <h2 className="text-xl font-semibold text-foreground mb-2">
              {podcast.title}
            </h2>
            <div className="text-sm text-muted-foreground space-y-1">
              <p>作成日: {formatDate(podcast.created_at)}</p>
              <p>更新日: {formatDate(podcast.updated_at)}</p>
              <p>状態: {podcast.status}</p>
            </div>
          </div>

          {podcast.error_message && (
            <div className="bg-red-50 border border-red-200 rounded-md p-3">
              <p className="text-sm text-red-700">
                エラー: {podcast.error_message}
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
            <h3 className="text-lg font-semibold text-foreground mb-4">台本</h3>
            <ScrollArea className="h-96">
              <div className="space-y-4">
                {podcast.script.map((turn, index) => (
                  <div key={index} className="flex space-x-3">
                    <div className="flex-shrink-0">
                      <span className="inline-flex items-center justify-center h-8 w-8 bg-primary text-primary-foreground rounded-full text-sm font-medium">
                        {turn.speaker}
                      </span>
                    </div>
                    <div className="flex-1">
                      <p className="text-sm text-foreground leading-relaxed">
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