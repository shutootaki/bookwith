import { Volume2, VolumeX } from 'lucide-react'
import React, { memo, useCallback, useMemo } from 'react'

import { VOLUME_SLIDER } from '../../constants/audio'
import {
  PODCAST_ICON_SIZES,
  PODCAST_KEYBOARD_SHORTCUTS,
} from '../../constants/podcast'
import { useTranslation } from '../../hooks/useTranslation'
import { formatVolumePercentage } from '../../utils/podcast'

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
    (e: React.ChangeEvent<HTMLInputElement>) => {
      onChange(parseFloat(e.target.value))
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

  const volumeIcon = useMemo(
    () => (isMuted ? <VolumeX /> : <Volume2 />),
    [isMuted],
  )

  return (
    <div className="flex items-center space-x-2">
      <button
        onClick={handleMuteToggle}
        disabled={disabled}
        className="text-muted-foreground focus:ring-primary rounded p-1 focus:outline-none focus:ring-2 disabled:cursor-not-allowed disabled:opacity-50"
        aria-label={
          isMuted
            ? t('podcast.audio_player.unmute')
            : t('podcast.audio_player.mute')
        }
        title={`${t('podcast.audio_player.mute_toggle')} (${
          PODCAST_KEYBOARD_SHORTCUTS.MUTE_TOGGLE
        })`}
      >
        <div className={PODCAST_ICON_SIZES.SM}>{volumeIcon}</div>
      </button>
      <div className="flex-1">
        <input
          type="range"
          min={VOLUME_SLIDER.MIN}
          max={VOLUME_SLIDER.MAX}
          step={VOLUME_SLIDER.STEP}
          value={volume}
          aria-label={t('podcast.volume_control.slider')}
          aria-valuetext={volumePercentage}
          onChange={handleVolumeChange}
          disabled={disabled}
          className="slider h-2 w-full cursor-pointer appearance-none rounded-lg bg-gray-200 disabled:cursor-not-allowed disabled:opacity-50"
          title={`${t('podcast.volume_control.adjust')} (${
            PODCAST_KEYBOARD_SHORTCUTS.VOLUME_UP
          }/${PODCAST_KEYBOARD_SHORTCUTS.VOLUME_DOWN})`}
        />
      </div>
      <span className="text-muted-foreground w-12 text-right text-sm">
        {volumePercentage}
      </span>
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

VolumeControl.displayName = 'VolumeControl'
