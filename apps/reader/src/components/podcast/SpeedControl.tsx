import { Gauge } from 'lucide-react'
import React, { memo, useCallback, useMemo } from 'react'

import { SPEED_OPTIONS } from '../../constants/audio'
import { PODCAST_ICON_SIZES, PODCAST_KEYBOARD_SHORTCUTS } from '../../constants/podcast'
import { useTranslation } from '../../hooks/useTranslation'
import { getSpeedLabel } from '../../utils/podcast'
import { Button } from '../ui/button'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '../ui/dropdown-menu'

interface SpeedControlProps {
  playbackRate: number
  onChange: (speed: number) => void
  disabled?: boolean
}

const SpeedControlComponent: React.FC<SpeedControlProps> = ({
  playbackRate,
  onChange,
  disabled = false,
}) => {
  const t = useTranslation()
  
  const currentSpeedLabel = useMemo(
    () => getSpeedLabel(playbackRate),
    [playbackRate],
  )
  
  const handleSpeedChange = useCallback(
    (speed: number) => {
      onChange(speed)
    },
    [onChange],
  )

  const menuItems = useMemo(
    () =>
      SPEED_OPTIONS.map((option) => (
        <DropdownMenuItem
          key={option.value}
          onClick={() => handleSpeedChange(option.value)}
          className={`cursor-pointer ${
            playbackRate === option.value
              ? 'bg-accent text-accent-foreground'
              : ''
          }`}
          aria-selected={playbackRate === option.value}
        >
          <span className="flex w-full items-center justify-between">
            {option.label}
            {playbackRate === option.value && (
              <span className="text-xs">✓</span>
            )}
          </span>
        </DropdownMenuItem>
      )),
    [SPEED_OPTIONS, playbackRate, handleSpeedChange],
  )

  return (
    <div className="flex items-center space-x-2">
      <Gauge className={`text-muted-foreground ${PODCAST_ICON_SIZES.SM}`} />
        <div className="flex-1">
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button
                variant="outline"
                size="sm"
                className="w-full justify-between"
                aria-label={t('podcast.audio_player.change_speed')}
                aria-haspopup="true"
                aria-expanded="false"
                disabled={disabled}
                title={`${t('podcast.speed_control.adjust')} (${PODCAST_KEYBOARD_SHORTCUTS.SPEED_UP}/${PODCAST_KEYBOARD_SHORTCUTS.SPEED_DOWN})`}
              >
                <span>
                  {t('podcast.audio_player.speed')}: {currentSpeedLabel}
                </span>
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent 
              align="end" 
              className="w-[140px]"
              aria-label={t('podcast.speed_control.options')}
            >
              {menuItems}
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
    </div>
  )
}

export const SpeedControl = memo(
  SpeedControlComponent,
  (prevProps, nextProps) => {
    return (
      prevProps.playbackRate === nextProps.playbackRate &&
      prevProps.disabled === nextProps.disabled &&
      prevProps.onChange === nextProps.onChange
    )
  },
)

SpeedControl.displayName = 'SpeedControl'
