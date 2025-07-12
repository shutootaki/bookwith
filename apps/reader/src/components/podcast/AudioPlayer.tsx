import React from 'react'

import { useAudioPlayer } from '../../hooks/useAudioPlayer'
import { useTranslation } from '../../hooks/useTranslation'
import { formatTime } from '../../utils/podcast'
import { Progress } from '../ui/progress'

import { AudioControls } from './AudioControls'
import { SpeedControl } from './SpeedControl'
import { VolumeControl } from './VolumeControl'

interface AudioPlayerProps {
  audioUrl: string
  title: string
  onPlay?: () => void
  onPause?: () => void
  onEnd?: () => void
  className?: string
}

export const AudioPlayer: React.FC<AudioPlayerProps> = ({
  audioUrl,
  title,
  onPlay,
  onPause,
  onEnd,
  className = '',
}) => {
  const { audioRef, isLoading, state, controls } = useAudioPlayer({
    audioUrl,
    onPlay,
    onPause,
    onEnd,
  })
  const t = useTranslation()

  const { isPlaying, currentTime, duration, volume, playbackRate, error } =
    state
  const {
    togglePlayPause,
    handleVolumeChange,
    handleSpeedChange,
    skipBack,
    skipForward,
    handleProgressClick,
  } = controls

  return (
    <div className={`space-y-4 ${className}`}>
      <audio ref={audioRef} src={audioUrl} preload="metadata" />

      {/* Title */}
      <div className="text-center">
        <h3
          className="text-foreground truncate text-lg font-semibold"
          title={title}
        >
          {title}
        </h3>
      </div>

      {/* Error Display */}
      {error && (
        <div className="rounded-md border border-red-200 bg-red-50 p-3">
          <p className="text-sm text-red-700">{error}</p>
        </div>
      )}

      {/* Progress Bar */}
      <div className="space-y-2">
        <div
          role="slider"
          aria-label={t('podcast.audio_player.position')}
          aria-valuemin={0}
          aria-valuemax={duration}
          aria-valuenow={currentTime}
          tabIndex={0}
          className="focus:ring-primary rounded focus:outline-none focus:ring-2 focus:ring-offset-2"
          onKeyDown={(e) => {
            if (e.key === 'ArrowLeft') {
              skipBack()
            } else if (e.key === 'ArrowRight') {
              skipForward()
            } else if (e.key === ' ') {
              e.preventDefault()
              togglePlayPause()
            }
          }}
        >
          <Progress
            value={duration ? (currentTime / duration) * 100 : 0}
            aria-valuetext={formatTime(currentTime)}
            className="h-2 cursor-pointer"
            onClick={handleProgressClick}
          />
        </div>
        <div className="text-muted-foreground flex justify-between text-sm">
          <span aria-label={t('podcast.audio_player.current_time')}>
            {formatTime(currentTime)}
          </span>
          <span aria-label={t('podcast.audio_player.total_time')}>
            {formatTime(duration)}
          </span>
        </div>
      </div>

      {/* Controls */}
      <AudioControls
        isPlaying={isPlaying}
        isLoading={isLoading}
        audioUrl={audioUrl}
        onTogglePlayPause={togglePlayPause}
        onSkipBack={skipBack}
        onSkipForward={skipForward}
      />

      {/* Volume Control */}
      <VolumeControl
        volume={volume}
        onChange={handleVolumeChange}
        disabled={!audioUrl || isLoading}
      />

      {/* Speed Control */}
      <SpeedControl
        playbackRate={playbackRate}
        onChange={handleSpeedChange}
        disabled={!audioUrl || isLoading}
      />
    </div>
  )
}

export default AudioPlayer
