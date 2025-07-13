import React, { memo } from 'react'

import { PODCAST_KEYBOARD_SHORTCUTS } from '../../constants/podcast'
import { useAudioPlayer } from '../../hooks/podcast/useAudioPlayer'
import { useTranslation } from '../../hooks/useTranslation'
import { formatTime } from '../../utils/podcast'
import { Alert, AlertDescription } from '../ui/alert'
import { Progress } from '../ui/progress'

import { AudioControls } from './AudioControls'
import { SpeedControl } from './SpeedControl'
import { VolumeControl } from './VolumeControl'

export interface AudioPlayerProps {
  audioUrl: string
  title: string
  onPlay?: () => void
  onPause?: () => void
  onEnd?: () => void
  onTimeUpdate?: (currentTime: number) => void
  onSeek?: (time: number) => void
}

const AudioPlayerComponent: React.FC<AudioPlayerProps> = ({
  audioUrl,
  title,
  onPlay,
  onPause,
  onEnd,
  onTimeUpdate,
  onSeek,
}) => {
  const { audioRef, isLoading, isMetadataLoaded, state, controls } =
    useAudioPlayer({
      onPlay,
      onPause,
      onEnd,
      onTimeUpdate,
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
    seekToTime,
  } = controls

  // onSeekプロパティをseekToTimeに接続
  React.useEffect(() => {
    if (onSeek && seekToTime) {
      window.podcastSeekFunction = seekToTime
    }
    return () => {
      delete window.podcastSeekFunction
    }
  }, [onSeek, seekToTime])

  return (
    <div className="space-y-4 pb-4">
      <audio ref={audioRef} src={audioUrl} preload="metadata" />
      {/* Title */}
      <h3
        className="text-foreground text-md truncate font-semibold"
        title={title}
      >
        {title}
      </h3>

      {/* Error Display */}
      {error && (
        <Alert variant="destructive">
          <AlertDescription>{error}</AlertDescription>
        </Alert>
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
            switch (e.key) {
              case PODCAST_KEYBOARD_SHORTCUTS.SKIP_BACK:
                skipBack()
                break
              case PODCAST_KEYBOARD_SHORTCUTS.SKIP_FORWARD:
                skipForward()
                break
              case PODCAST_KEYBOARD_SHORTCUTS.PLAY_PAUSE:
                e.preventDefault()
                togglePlayPause()
                break
            }
          }}
        >
          <Progress
            value={
              duration && isMetadataLoaded ? (currentTime / duration) * 100 : 0
            }
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
            {isMetadataLoaded ? formatTime(duration) : '--:--'}
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

export const AudioPlayer = memo(AudioPlayerComponent)
