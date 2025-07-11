import { RefreshCw } from 'lucide-react'
import React, { useState } from 'react'
import { toast } from 'sonner'

import { usePodcastsByBook } from '../../hooks/useSWR/usePodcast'
import { createPodcast, retryPodcast } from '../../lib/apiHandler/podcastApiHandler'
import { components } from '../../lib/openapi-schema/schema'
import { reader, useReaderSnapshot } from '../../models'
import { Button } from '../ui/button'
import { Card } from '../ui/card'

import { PodcastDetail } from './PodcastDetail'
import { PodcastList } from './PodcastList'

type PodcastResponse = components['schemas']['PodcastResponse']

interface PodcastPaneProps {
  className?: string
}

export const PodcastPane: React.FC<PodcastPaneProps> = ({ className = '' }) => {
  const { focusedBookTab } = useReaderSnapshot()
  const [selectedPodcast, setSelectedPodcast] =
    useState<PodcastResponse | null>(null)
  const [isCreating, setIsCreating] = useState(false)
  const [retryingPodcastId, setRetryingPodcastId] = useState<string | null>(null)

  const { podcasts, isLoading, error, mutate } = usePodcastsByBook(
    focusedBookTab?.book.id,
  )

  const handleCreatePodcast = async () => {
    if (!focusedBookTab?.book.id) return

    setIsCreating(true)
    try {
      const result = await createPodcast(
        focusedBookTab.book.id,
        `${focusedBookTab.book.name}のポッドキャスト`,
      )

      if (result) {
        toast.success('ポッドキャストの生成を開始しました')
        mutate() // Refresh the podcast list
      } else {
        toast.error('ポッドキャストの生成に失敗しました')
      }
    } catch (error) {
      console.error('Error creating podcast:', error)
      toast.error('ポッドキャストの生成に失敗しました')
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
        toast.success('ポッドキャストの再生成を開始しました')
        mutate() // Refresh the podcast list
      } else {
        toast.error('ポッドキャストの再生成に失敗しました')
      }
    } catch (error) {
      console.error('Error retrying podcast:', error)
      toast.error('ポッドキャストの再生成に失敗しました')
    } finally {
      setRetryingPodcastId(null)
    }
  }

  if (!focusedBookTab) {
    return (
      <div className={`py-8 text-center ${className}`}>
        <p className="text-muted-foreground">
          書籍を選択してポッドキャストを生成できます
        </p>
      </div>
    )
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
    <div className={`space-y-6 ${className}`}>
      {/* Current Book Info */}
      <Card className="p-4">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-foreground mb-1 font-semibold">
              {focusedBookTab.book.name}
            </h3>
            <p className="text-muted-foreground text-sm">
              {focusedBookTab.book.author || '作者不明'}
            </p>
          </div>

          <Button
            onClick={handleCreatePodcast}
            disabled={
              isCreating || podcasts.some((p) => p.status === 'PROCESSING')
            }
            className="flex items-center space-x-2"
          >
            {isCreating ? (
              <>
                <RefreshCw className="h-4 w-4 animate-spin" />
                <span>生成中...</span>
              </>
            ) : (
              <span>ポッドキャスト生成</span>
            )}
          </Button>
        </div>
      </Card>

      {/* Podcast List */}
      <div>
        <div className="mb-4 flex items-center justify-between">
          <h3 className="text-foreground font-semibold">ポッドキャスト一覧</h3>
          <Button
            variant="outline"
            size="sm"
            onClick={() => mutate()}
            disabled={isLoading}
            className="flex items-center space-x-1"
          >
            <RefreshCw
              className={`h-4 w-4 ${isLoading ? 'animate-spin' : ''}`}
            />
            <span>更新</span>
          </Button>
        </div>

        {error && (
          <Card className="mb-4 border-red-200 bg-red-50 p-4">
            <p className="text-sm text-red-700">
              ポッドキャストの読み込みに失敗しました
            </p>
            <p className="mt-1 text-xs text-red-600">{error.message}</p>
            <Button
              variant="outline"
              size="sm"
              onClick={() => mutate()}
              className="mt-2"
            >
              再試行
            </Button>
          </Card>
        )}

        {isLoading ? (
          <Card className="p-8">
            <div className="space-y-3 text-center">
              <RefreshCw className="text-primary mx-auto h-6 w-6 animate-spin" />
              <div>
                <p className="text-foreground text-sm font-medium">
                  読み込み中...
                </p>
                <p className="text-muted-foreground text-xs">
                  ポッドキャスト情報を取得しています
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
    </div>
  )
}

export default PodcastPane
