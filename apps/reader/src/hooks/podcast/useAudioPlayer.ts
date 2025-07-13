import { useEffect, useRef, useState, useCallback } from 'react'

import { AUDIO_EVENTS } from '../../constants/audio'
import { PODCAST_ERROR_KEYS } from '../../constants/podcast'
import { reader, useReaderSnapshot } from '../../models'

import { useAudioControls } from './useAudioControls'

export interface AudioPlayerState {
  isPlaying: boolean
  currentTime: number
  duration: number
  volume: number
  playbackRate: number
  error: string | null
}

interface AudioPlayerCallbacks {
  onPlay?: () => void
  onPause?: () => void
  onEnd?: () => void
  onTimeUpdate?: (currentTime: number) => void
}

/**
 * オーディオプレイヤーのロジックを管理するカスタムフック
 */
export const useAudioPlayer = ({
  onPlay,
  onPause,
  onEnd,
  onTimeUpdate,
}: AudioPlayerCallbacks) => {
  const audioRef = useRef<HTMLAudioElement>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [isMetadataLoaded, setIsMetadataLoaded] = useState(false)
  const { podcast } = useReaderSnapshot()

  // Valtio状態から値を取得
  const { isPlaying, currentTime, duration, volume, playbackRate, error } =
    podcast as AudioPlayerState

  // 音量の更新
  useEffect(() => {
    if (audioRef.current) {
      audioRef.current.volume = volume
    }
  }, [volume])

  // 再生速度の更新
  useEffect(() => {
    if (audioRef.current) {
      audioRef.current.playbackRate = playbackRate
    }
  }, [playbackRate])

  // オーディオイベントの設定
  useEffect(() => {
    const audio = audioRef.current
    if (!audio) return

    const handleTimeUpdate = () => {
      reader.updatePodcastTime(audio.currentTime)
      onTimeUpdate?.(audio.currentTime)
    }

    const handleLoadedMetadata = () => {
      reader.updatePodcastTime(audio.currentTime, audio.duration)
      setIsMetadataLoaded(true)
      setIsLoading(false)
    }

    const handleEnded = () => {
      reader.stopPodcast()
      onEnd?.()
    }

    const handleLoadStart = () => {
      setIsLoading(true)
      setIsMetadataLoaded(false)
    }

    const handleCanPlay = () => {
      setIsLoading(false)
    }

    const handleError = () => {
      reader.setPodcastError(PODCAST_ERROR_KEYS.PLAYBACK_FAILED)
      setIsLoading(false)
      setIsMetadataLoaded(false)
    }

    // イベントリスナーの登録
    audio.addEventListener(AUDIO_EVENTS.TIME_UPDATE, handleTimeUpdate)
    audio.addEventListener(AUDIO_EVENTS.LOADED_METADATA, handleLoadedMetadata)
    audio.addEventListener(AUDIO_EVENTS.ENDED, handleEnded)
    audio.addEventListener(AUDIO_EVENTS.LOAD_START, handleLoadStart)
    audio.addEventListener(AUDIO_EVENTS.CAN_PLAY, handleCanPlay)
    audio.addEventListener(AUDIO_EVENTS.ERROR, handleError)

    return () => {
      audio.removeEventListener(AUDIO_EVENTS.TIME_UPDATE, handleTimeUpdate)
      audio.removeEventListener(
        AUDIO_EVENTS.LOADED_METADATA,
        handleLoadedMetadata,
      )
      audio.removeEventListener(AUDIO_EVENTS.ENDED, handleEnded)
      audio.removeEventListener(AUDIO_EVENTS.LOAD_START, handleLoadStart)
      audio.removeEventListener(AUDIO_EVENTS.CAN_PLAY, handleCanPlay)
      audio.removeEventListener(AUDIO_EVENTS.ERROR, handleError)
    }
  }, [onEnd, onTimeUpdate])

  // オーディオコントロールのフックを使用
  const controls = useAudioControls({
    audioRef,
    duration,
    onTimeUpdate: reader.updatePodcastTime,
    onPlayPause: async () => {
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
          reader.setPodcastError(PODCAST_ERROR_KEYS.PLAYBACK_FAILED)
        }
      }
    },
    onVolumeChange: (volume: number) => reader.setPodcastVolume(volume),
    onSpeedChange: (rate) => reader.setPodcastPlaybackRate(rate),
  })

  // シーク処理（スライダー用）
  const handleSeek = useCallback((value: number[]) => {
    if (!audioRef.current) return
    const newTime = value[0]
    if (newTime !== undefined) {
      audioRef.current.currentTime = newTime
      reader.updatePodcastTime(newTime)
    }
  }, [])

  // 特定時間へのシーク（スクリプトクリック用）
  const seekToTime = useCallback(
    (time: number) => {
      if (!audioRef.current || !isMetadataLoaded) return
      audioRef.current.currentTime = time
      reader.updatePodcastTime(time)
    },
    [isMetadataLoaded],
  )

  return {
    audioRef,
    isLoading,
    isMetadataLoaded,
    state: {
      isPlaying,
      currentTime,
      duration,
      volume,
      playbackRate,
      error,
    },
    controls: {
      ...controls,
      handleSeek,
      seekToTime,
    },
  }
}
