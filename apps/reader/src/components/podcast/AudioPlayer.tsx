import { Pause, Play, SkipBack, SkipForward, Volume2 } from 'lucide-react'
import React, { useEffect, useRef, useState } from 'react'

import { reader, useReaderSnapshot } from '../../models'
import { Button } from '../ui/button'
import { Progress } from '../ui/progress'

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
  const audioRef = useRef<HTMLAudioElement>(null)
  const [isLoading, setIsLoading] = useState(false)
  const { podcast } = useReaderSnapshot()

  // Use Valtio state
  const { isPlaying, currentTime, duration, volume, error } = podcast

  // Update current time
  useEffect(() => {
    const audio = audioRef.current
    if (!audio) return

    const handleTimeUpdate = () => {
      reader.updatePodcastTime(audio.currentTime)
    }

    const handleLoadedMetadata = () => {
      reader.updatePodcastTime(audio.currentTime, audio.duration)
      setIsLoading(false)
    }

    const handleEnded = () => {
      reader.stopPodcast()
      onEnd?.()
    }

    const handleLoadStart = () => {
      setIsLoading(true)
    }

    const handleCanPlay = () => {
      setIsLoading(false)
    }

    audio.addEventListener('timeupdate', handleTimeUpdate)
    audio.addEventListener('loadedmetadata', handleLoadedMetadata)
    audio.addEventListener('ended', handleEnded)
    audio.addEventListener('loadstart', handleLoadStart)
    audio.addEventListener('canplay', handleCanPlay)

    return () => {
      audio.removeEventListener('timeupdate', handleTimeUpdate)
      audio.removeEventListener('loadedmetadata', handleLoadedMetadata)
      audio.removeEventListener('ended', handleEnded)
      audio.removeEventListener('loadstart', handleLoadStart)
      audio.removeEventListener('canplay', handleCanPlay)
    }
  }, [onEnd])

  // Update audio volume
  useEffect(() => {
    if (audioRef.current) {
      audioRef.current.volume = volume
    }
  }, [volume])

  const togglePlayPause = async () => {
    if (!audioRef.current) return

    if (isPlaying) {
      audioRef.current.pause()
      reader.pausePodcast()
      onPause?.()
    } else {
      try {
        await audioRef.current.play()
        reader.playPodcast()
        onPlay?.()
      } catch (error) {
        console.error('Error playing audio:', error)
        reader.setPodcastError('音声の再生に失敗しました')
      }
    }
  }

  const handleSeek = (value: number[]) => {
    if (!audioRef.current) return
    const newTime = value[0]
    if (newTime !== undefined) {
      audioRef.current.currentTime = newTime
      reader.updatePodcastTime(newTime)
    }
  }

  const handleVolumeChange = (value: number[]) => {
    const newVolume = value[0]
    if (newVolume !== undefined) {
      reader.setPodcastVolume(newVolume)
    }
  }

  // --- Skip Back / Forward helpers (support long press) ---
  const seek = (delta: number) => {
    if (!audioRef.current) return
    const newTime = Math.min(
      Math.max(0, audioRef.current.currentTime + delta),
      duration,
    )
    audioRef.current.currentTime = newTime
    reader.updatePodcastTime(newTime)
  }

  const skipBack = () => seek(-10)
  const skipForward = () => seek(10)

  const useLongPress = (
    action: () => void,
    { interval = 200 }: { interval?: number } = {},
  ) => {
    const timer = useRef<NodeJS.Timeout | null>(null)

    const start = () => {
      action()
      timer.current = setInterval(action, interval)
    }
    const stop = () => {
      if (timer.current) clearInterval(timer.current)
      timer.current = null
    }
    return { onPointerDown: start, onPointerUp: stop, onPointerLeave: stop }
  }

  const longPressBack = useLongPress(skipBack)
  const longPressForward = useLongPress(skipForward)

  const formatTime = (time: number) => {
    if (isNaN(time)) return '0:00'
    const minutes = Math.floor(time / 60)
    const seconds = Math.floor(time % 60)
    return `${minutes}:${seconds.toString().padStart(2, '0')}`
  }

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
          aria-label="音声再生位置"
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
            aria-valuetext={`${formatTime(currentTime)}`}
            className="h-2 cursor-pointer"
            onClick={(e) => {
              if (!audioRef.current || !duration) return
              const rect = e.currentTarget.getBoundingClientRect()
              const x = e.clientX - rect.left
              const percentage = x / rect.width
              const newTime = percentage * duration
              handleSeek([newTime])
            }}
          />
        </div>
        <div className="text-muted-foreground flex justify-between text-sm">
          <span aria-label="現在の再生時間">{formatTime(currentTime)}</span>
          <span aria-label="総再生時間">{formatTime(duration)}</span>
        </div>
      </div>

      {/* Controls */}
      <div
        className="flex flex-wrap items-center justify-center gap-4"
        role="group"
        aria-label="音声コントロール"
      >
        <Button
          variant="ghost"
          size="icon"
          onClick={skipBack}
          disabled={!audioUrl || isLoading}
          aria-label="10秒戻る"
          {...longPressBack}
        >
          <SkipBack className="h-4 w-4" />
        </Button>

        <Button
          variant="default"
          size="icon"
          onClick={togglePlayPause}
          disabled={!audioUrl || isLoading}
          className="h-12 w-12"
          aria-label={isPlaying ? '一時停止' : '再生'}
        >
          {isLoading ? (
            <div
              className="h-4 w-4 animate-spin rounded-full border-2 border-current border-t-transparent"
              aria-label="読み込み中"
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
          onClick={skipForward}
          disabled={!audioUrl || isLoading}
          aria-label="10秒進む"
          {...longPressForward}
        >
          <SkipForward className="h-4 w-4" />
        </Button>
      </div>

      {/* Volume Control */}
      <div className="flex items-center space-x-2">
        <Volume2 className="text-muted-foreground h-4 w-4" />
        <div className="flex-1">
          <input
            type="range"
            min="0"
            max="1"
            step="0.1"
            value={volume}
            aria-valuetext={`${Math.round(volume * 100)}%`}
            onChange={(e) => handleVolumeChange([parseFloat(e.target.value)])}
            className="slider h-2 w-full cursor-pointer appearance-none rounded-lg bg-gray-200"
          />
        </div>
        <span className="text-muted-foreground w-8 text-sm">
          {Math.round(volume * 100)}%
        </span>
      </div>
    </div>
  )
}

export default AudioPlayer
