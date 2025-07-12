import { Volume2 } from 'lucide-react'
import React, { memo, useCallback } from 'react'

import { VOLUME_SLIDER } from '../../constants/audio'
import { formatVolumePercentage } from '../../utils/podcast'

interface VolumeControlProps {
  volume: number
  onChange: (value: number) => void
  disabled?: boolean
}

export const VolumeControl = memo<VolumeControlProps>(
  ({ volume, onChange, disabled = false }) => {
    const handleVolumeChange = useCallback(
      (e: React.ChangeEvent<HTMLInputElement>) => {
        onChange(parseFloat(e.target.value))
      },
      [onChange],
    )

    return (
      <div className="flex items-center space-x-2">
        <Volume2 className="text-muted-foreground h-4 w-4" />
        <div className="flex-1">
          <input
            type="range"
            min={VOLUME_SLIDER.MIN}
            max={VOLUME_SLIDER.MAX}
            step={VOLUME_SLIDER.STEP}
            value={volume}
            aria-valuetext={formatVolumePercentage(volume)}
            onChange={handleVolumeChange}
            disabled={disabled}
            className="slider h-2 w-full cursor-pointer appearance-none rounded-lg bg-gray-200 disabled:cursor-not-allowed disabled:opacity-50"
          />
        </div>
        <span className="text-muted-foreground w-8 text-sm">
          {formatVolumePercentage(volume)}
        </span>
      </div>
    )
  },
)

VolumeControl.displayName = 'VolumeControl'
