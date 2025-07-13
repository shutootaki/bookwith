import { Pause, Play, SkipBack, SkipForward } from 'lucide-react'
import React, { memo } from 'react'

import {
  PODCAST_ANIMATIONS,
  PODCAST_ICON_SIZES,
  PODCAST_UI_CLASSES,
} from '../../constants/podcast'
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

export const AudioControls = memo<AudioControlsProps>(
  ({
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
          <SkipBack className={PODCAST_ICON_SIZES.SM} />
        </Button>

        <Button
          variant="default"
          size="icon"
          onClick={onTogglePlayPause}
          disabled={!audioUrl || isLoading}
          className={PODCAST_UI_CLASSES.PLAY_BUTTON}
          aria-label={isPlaying ? t('podcast.pause') : t('podcast.play')}
        >
          {isLoading ? (
            <div
              className={`${PODCAST_ICON_SIZES.SM} ${PODCAST_ANIMATIONS.SPIN} rounded-full border-2 border-current border-t-transparent`}
              aria-label={t('podcast.audio_player.loading')}
            />
          ) : isPlaying ? (
            <Pause className={PODCAST_ICON_SIZES.MD} />
          ) : (
            <Play className={PODCAST_ICON_SIZES.MD} />
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
          <SkipForward className={PODCAST_ICON_SIZES.SM} />
        </Button>
      </div>
    )
  },
)

AudioControls.displayName = 'AudioControls'
