import { Pause, Play, SkipBack, SkipForward } from 'lucide-react'
import React from 'react'

import { useLongPress } from '../../hooks/useLongPress'
import { useTranslation } from '../../hooks/useTranslation'
import { Button } from '../ui/button'

interface AudioControlsProps {
  isPlaying: boolean
  isLoading: boolean
  audioUrl: string
  onTogglePlayPause: () => void
  onSkipBack: () => void
  onSkipForward: () => void
}

export const AudioControls: React.FC<AudioControlsProps> = ({
  isPlaying,
  isLoading,
  audioUrl,
  onTogglePlayPause,
  onSkipBack,
  onSkipForward,
}) => {
  const t = useTranslation()

  // 長押し対応
  const longPressBack = useLongPress(onSkipBack)
  const longPressForward = useLongPress(onSkipForward)

  return (
    <div
      className="flex flex-wrap items-center justify-center gap-4"
      role="group"
      aria-label={t('podcast.audio_player.controls')}
    >
      <Button
        variant="ghost"
        size="icon"
        onClick={onSkipBack}
        disabled={!audioUrl || isLoading}
        aria-label={t('podcast.audio_player.skip_back')}
        {...longPressBack}
      >
        <SkipBack className="h-4 w-4" />
      </Button>

      <Button
        variant="default"
        size="icon"
        onClick={onTogglePlayPause}
        disabled={!audioUrl || isLoading}
        className="h-12 w-12"
        aria-label={isPlaying ? t('podcast.pause') : t('podcast.play')}
      >
        {isLoading ? (
          <div
            className="h-4 w-4 animate-spin rounded-full border-2 border-current border-t-transparent"
            aria-label={t('podcast.audio_player.loading')}
          />
        ) : isPlaying ? (
          <Pause className="h-6 w-6" />
        ) : (
          <Play className="h-6 w-6" />
        )}
      </Button>

      <Button
        variant="ghost"
        size="icon"
        onClick={onSkipForward}
        disabled={!audioUrl || isLoading}
        aria-label={t('podcast.audio_player.skip_forward')}
        {...longPressForward}
      >
        <SkipForward className="h-4 w-4" />
      </Button>
    </div>
  )
}
