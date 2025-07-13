import { Volume2, VolumeX } from 'lucide-react'
import React, { memo, useCallback, useMemo } from 'react'

import { VOLUME_SLIDER } from '../../constants/audio'
import {
  PODCAST_ICON_SIZES,
  PODCAST_KEYBOARD_SHORTCUTS,
} from '../../constants/podcast'
import { useTranslation } from '../../hooks/useTranslation'
import { formatVolumePercentage } from '../../utils/podcast'
import { Button } from '../ui/button'
import { Slider } from '../ui/slider'

interface VolumeControlProps {
  volume: number
  onChange: (value: number) => void
  disabled?: boolean
}

const VolumeControlComponent: React.FC<VolumeControlProps> = ({
  volume,
  onChange,
  disabled = false,
}) => {
  const t = useTranslation()
  const isMuted = volume === 0

  const handleVolumeChange = useCallback(
    (value: number[]) => {
      if (value[0] !== undefined) {
        onChange(value[0])
      }
    },
    [onChange],
  )

  const handleMuteToggle = useCallback(() => {
    onChange(isMuted ? 1 : 0)
  }, [isMuted, onChange])

  const volumePercentage = useMemo(
    () => formatVolumePercentage(volume),
    [volume],
  )

  const volumeIcon = (className: string) =>
    isMuted ? (
      <VolumeX className={className} />
    ) : (
      <Volume2 className={className} />
    )

  return (
    <div className="flex items-center space-x-2">
      <Button
        variant="ghost"
        size="icon"
        onClick={handleMuteToggle}
        disabled={disabled}
        className="h-4 w-4"
        aria-label={
          isMuted
            ? t('podcast.audio_player.unmute')
            : t('podcast.audio_player.mute')
        }
        title={`${t('podcast.audio_player.mute_toggle')} (${
          PODCAST_KEYBOARD_SHORTCUTS.MUTE_TOGGLE
        })`}
      >
        <span>{volumeIcon(PODCAST_ICON_SIZES.SM)}</span>
      </Button>
      <div className="flex-1">
        <Slider
          min={VOLUME_SLIDER.MIN}
          max={VOLUME_SLIDER.MAX}
          step={VOLUME_SLIDER.STEP}
          value={[volume]}
          onValueChange={handleVolumeChange}
          disabled={disabled}
          aria-label={t('podcast.volume_control.slider')}
          aria-valuetext={volumePercentage}
          className="w-full cursor-pointer"
          title={`${t('podcast.volume_control.adjust')} (${
            PODCAST_KEYBOARD_SHORTCUTS.VOLUME_UP
          }/${PODCAST_KEYBOARD_SHORTCUTS.VOLUME_DOWN})`}
        />
      </div>
    </div>
  )
}

export const VolumeControl = memo(
  VolumeControlComponent,
  (prevProps, nextProps) => {
    return (
      prevProps.volume === nextProps.volume &&
      prevProps.disabled === nextProps.disabled &&
      prevProps.onChange === nextProps.onChange
    )
  },
)
