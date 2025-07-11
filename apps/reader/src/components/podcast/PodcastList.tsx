import { motion } from 'framer-motion'
import { AlertCircle, Clock, Play, RefreshCw } from 'lucide-react'
import React from 'react'

import { usePodcastStatus } from '../../hooks/useSWR/usePodcast'
import { components } from '../../lib/openapi-schema/schema'
import { Button } from '../ui/button'
import { Card } from '../ui/card'
import { Progress } from '../ui/progress'

type PodcastResponse = components['schemas']['PodcastResponse']

interface PodcastListProps {
  podcasts: PodcastResponse[]
  onPlay: (podcast: PodcastResponse) => void
  onRetry?: (podcastId: string) => void
  retryingPodcastId?: string | null
  className?: string
}

// Status helpers (color / icon / text)
const getStatusColor = (status: string) => {
  switch (status) {
    case 'COMPLETED':
      return 'text-green-600 bg-green-50'
    case 'PROCESSING':
      return 'text-blue-600 bg-blue-50'
    case 'PENDING':
      return 'text-yellow-600 bg-yellow-50'
    case 'FAILED':
      return 'text-red-600 bg-red-50'
    default:
      return 'text-gray-600 bg-gray-50'
  }
}

const getStatusIcon = (status: string) => {
  switch (status) {
    case 'COMPLETED':
      return <Play className="h-4 w-4" />
    case 'PROCESSING':
      return <RefreshCw className="h-4 w-4 animate-spin" />
    case 'PENDING':
      return <Clock className="h-4 w-4" />
    case 'FAILED':
      return <AlertCircle className="h-4 w-4" />
    default:
      return <Clock className="h-4 w-4" />
  }
}

const getStatusText = (status: string) => {
  switch (status) {
    case 'COMPLETED':
      return '完了'
    case 'PROCESSING':
      return '生成中'
    case 'PENDING':
      return '待機中'
    case 'FAILED':
      return '失敗'
    default:
      return '不明'
  }
}

export const PodcastList: React.FC<PodcastListProps> = ({
  podcasts,
  onPlay,
  onRetry,
  retryingPodcastId,
  className = '',
}) => {
  if (podcasts.length === 0) {
    return (
      <div className={`py-8 text-center ${className}`}>
        <p className="text-muted-foreground">まだポッドキャストがありません</p>
      </div>
    )
  }

  return (
    <div className={`space-y-3 ${className}`} role="list" aria-live="polite">
      {podcasts.map((p) => (
        <PodcastCard 
          key={p.id} 
          podcast={p} 
          onPlay={onPlay} 
          onRetry={onRetry} 
          isRetrying={retryingPodcastId === p.id}
        />
      ))}
    </div>
  )
}

interface CardProps {
  podcast: PodcastResponse
  onPlay: (podcast: PodcastResponse) => void
  onRetry?: (id: string) => void
  isRetrying?: boolean
}

const PodcastCard: React.FC<CardProps> = ({ podcast, onPlay, onRetry, isRetrying = false }) => {
  // Poll status if processing
  const { status } = usePodcastStatus(
    podcast.id,
    podcast.status === 'PROCESSING',
  )

  const currentStatus = status?.status ?? podcast.status

  const getProgress = () => {
    if (!status) return undefined
    if (
      status.status === 'PROCESSING' &&
      status.script_turn_count &&
      status.script_character_count
    ) {
      // naive progress: turns generated / expected (unknown) => fallback undefined
    }
    return undefined
  }

  const progress = getProgress()

  return (
    <motion.div
      role="listitem"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
    >
      <Card className="p-4 transition-shadow hover:shadow-md">
        <div className="flex items-start justify-between">
          <div className="min-w-0 flex-1">
            <h3 className="text-foreground mb-1 truncate font-semibold">
              {podcast.title}
            </h3>

            <div className="mb-2 flex items-center space-x-2">
              <div
                className={`inline-flex items-center rounded-full px-2 py-1 text-xs font-medium ${getStatusColor(
                  currentStatus,
                )}`}
              >
                {getStatusIcon(currentStatus)}
                <span className="ml-1">{getStatusText(currentStatus)}</span>
              </div>
            </div>

            {currentStatus === 'PROCESSING' && (
              <div className="mb-2">
                <Progress
                  value={progress ?? 100}
                  className="h-2 animate-pulse"
                />
                <p className="text-muted-foreground mt-1 text-xs">
                  ポッドキャストを生成中...
                </p>
              </div>
            )}

            {currentStatus === 'FAILED' && podcast.error_message && (
              <div className="mb-2">
                <p className="rounded bg-red-50 p-2 text-xs text-red-600">
                  エラー: {podcast.error_message}
                </p>
              </div>
            )}

            <div className="text-muted-foreground text-xs">
              <p>
                作成日:{' '}
                {new Date(podcast.created_at).toLocaleDateString('ja-JP')}
              </p>
              {podcast.updated_at !== podcast.created_at && (
                <p>
                  更新日:{' '}
                  {new Date(podcast.updated_at).toLocaleDateString('ja-JP')}
                </p>
              )}
            </div>
          </div>

          <div className="ml-4 flex items-center space-x-2">
            {currentStatus === 'COMPLETED' && podcast.audio_url && (
              <Button
                variant="default"
                size="sm"
                onClick={() => onPlay(podcast)}
                className="flex items-center space-x-1"
              >
                <Play className="h-4 w-4" />
                <span>再生</span>
              </Button>
            )}

            {currentStatus === 'FAILED' && onRetry && (
              <Button
                variant="outline"
                size="sm"
                onClick={() => onRetry(podcast.id)}
                disabled={isRetrying}
                className="flex items-center space-x-1"
              >
                <RefreshCw className={`h-4 w-4 ${isRetrying ? 'animate-spin' : ''}`} />
                <span>{isRetrying ? '再生成中...' : '再試行'}</span>
              </Button>
            )}
          </div>
        </div>
      </Card>
    </motion.div>
  )
}

export default PodcastList
