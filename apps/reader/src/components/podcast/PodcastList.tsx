import { motion } from 'framer-motion'
import { Play, RefreshCw } from 'lucide-react'
import React from 'react'

import { usePodcastStatus } from '../../hooks/useSWR/usePodcast'
import { useTranslation } from '../../hooks/useTranslation'
import { PodcastResponse } from '../../types/podcast'
import {
  getStatusColor,
  getStatusIcon,
  getStatusTextKey,
  formatDateOnly,
  calculateProgress,
} from '../../utils/podcast'
import { Button } from '../ui/button'
import { Card } from '../ui/card'
import { Progress } from '../ui/progress'

interface PodcastListProps {
  podcasts: PodcastResponse[]
  onPlay: (podcast: PodcastResponse) => void
  onRetry?: (podcastId: string) => void
  retryingPodcastId?: string | null
  className?: string
}

interface PodcastCardProps {
  podcast: PodcastResponse
  onPlay: (podcast: PodcastResponse) => void
  onRetry?: (id: string) => void
  isRetrying?: boolean
}

export const PodcastList: React.FC<PodcastListProps> = ({
  podcasts,
  onPlay,
  onRetry,
  retryingPodcastId,
  className = '',
}) => {
  const t = useTranslation()

  if (podcasts.length === 0) {
    return (
      <div className={`py-8 text-center ${className}`}>
        <p className="text-muted-foreground">{t('podcast.list.empty')}</p>
      </div>
    )
  }

  return (
    <div className={`space-y-2 ${className}`} role="list" aria-live="polite">
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

const PodcastCard: React.FC<PodcastCardProps> = ({
  podcast,
  onPlay,
  onRetry,
  isRetrying = false,
}) => {
  const t = useTranslation()

  // Poll status if processing
  const { status } = usePodcastStatus(
    podcast.id,
    podcast.status === 'PROCESSING',
  )

  const currentStatus = status?.status ?? podcast.status
  const progress = calculateProgress(status)
  const StatusIcon = getStatusIcon(currentStatus)

  return (
    <motion.div
      role="listitem"
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.2 }}
    >
      <Card className="p-3 transition-shadow hover:shadow-md">
        <div className="flex items-start justify-between">
          <div className="min-w-0 flex-1">
            <h3 className="text-foreground mb-1 truncate text-sm font-medium leading-tight">
              {podcast.title}
            </h3>

            <div className="mb-2 flex items-center space-x-2">
              <div
                className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${getStatusColor(
                  currentStatus,
                )}`}
              >
                <StatusIcon className="h-4 w-4" />
                <span className="ml-1">
                  {t(getStatusTextKey(currentStatus))}
                </span>
              </div>
            </div>

            {currentStatus === 'PROCESSING' && (
              <div className="mb-2">
                <Progress
                  value={progress ?? 100}
                  className="h-1.5 animate-pulse"
                />
                <p className="text-muted-foreground mt-1 text-xs">
                  {t('podcast.list.generating')}
                </p>
              </div>
            )}

            {currentStatus === 'FAILED' && podcast.error_message && (
              <div className="mb-2">
                <p className="rounded bg-red-50 p-2 text-xs text-red-600">
                  {t('podcast.detail.error')}: {podcast.error_message}
                </p>
              </div>
            )}

            <div className="text-muted-foreground text-xs">
              <p>
                {t('podcast.list.created_date')}:{' '}
                {formatDateOnly(podcast.created_at)}
              </p>
              {podcast.updated_at !== podcast.created_at && (
                <p>
                  {t('podcast.list.updated_date')}:{' '}
                  {formatDateOnly(podcast.updated_at)}
                </p>
              )}
            </div>
          </div>

          <div className="ml-2 flex items-center space-x-1">
            {currentStatus === 'COMPLETED' && podcast.audio_url && (
              <Button
                variant="default"
                size="sm"
                onClick={() => onPlay(podcast)}
                className="flex h-7 items-center space-x-1 px-2"
                aria-label={`${podcast.title}を再生`}
              >
                <Play className="h-3 w-3" aria-hidden="true" />
                <span className="text-xs">{t('podcast.play')}</span>
              </Button>
            )}

            {currentStatus === 'FAILED' && onRetry && (
              <Button
                variant="outline"
                size="sm"
                onClick={() => onRetry(podcast.id)}
                disabled={isRetrying}
                className="flex h-7 items-center space-x-1 px-2"
                aria-label={
                  isRetrying
                    ? `${podcast.title}を再生成中`
                    : `${podcast.title}を再試行`
                }
              >
                <RefreshCw
                  className={`h-3 w-3 ${isRetrying ? 'animate-spin' : ''}`}
                  aria-hidden="true"
                />
                <span className="text-xs">
                  {isRetrying
                    ? t('podcast.list.retrying')
                    : t('podcast.list.retry')}
                </span>
              </Button>
            )}
          </div>
        </div>
      </Card>
    </motion.div>
  )
}

export default PodcastList
