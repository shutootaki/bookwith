import { Gauge } from 'lucide-react'
import React, { memo } from 'react'

import { SPEED_OPTIONS } from '../../constants/audio'
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

export const SpeedControl = memo<SpeedControlProps>(
  ({ playbackRate, onChange, disabled = false }) => {
    const t = useTranslation()

    return (
      <div className="flex items-center space-x-2">
        <Gauge className="text-muted-foreground h-4 w-4" />
        <div className="flex-1">
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button
                variant="outline"
                size="sm"
                className="w-full justify-between"
                aria-label={t('podcast.audio_player.change_speed')}
                disabled={disabled}
              >
                <span>
                  {t('podcast.audio_player.speed')}:{' '}
                  {getSpeedLabel(playbackRate)}
                </span>
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="w-[140px]">
              {SPEED_OPTIONS.map((option) => (
                <DropdownMenuItem
                  key={option.value}
                  onClick={() => onChange(option.value)}
                  className={`cursor-pointer ${
                    playbackRate === option.value ? 'bg-accent' : ''
                  }`}
                >
                  {option.label}
                </DropdownMenuItem>
              ))}
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </div>
    )
  },
)

SpeedControl.displayName = 'SpeedControl'
