import { useEffect, useRef, useState, useCallback } from 'react'

import { AUDIO_CONTROLS, AUDIO_EVENTS } from '../constants/audio'
import { reader, useReaderSnapshot } from '../models'
import { seekAudio } from '../utils/podcast'

interface AudioPlayerCallbacks {
  onPlay?: () => void
  onPause?: () => void
  onEnd?: () => void
}

/**
 * オーディオプレイヤーのロジックを管理するカスタムフック
 */
export const useAudioPlayer = ({
  onPlay,
  onPause,
  onEnd,
}: AudioPlayerCallbacks) => {
  const audioRef = useRef<HTMLAudioElement>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [isMetadataLoaded, setIsMetadataLoaded] = useState(false)
  const { podcast } = useReaderSnapshot()

  // Valtio状態から値を取得
  const { isPlaying, currentTime, duration, volume, playbackRate, error } =
    podcast

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
      reader.setPodcastError('音声の読み込みに失敗しました')
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
  }, [onEnd])

  // 再生/一時停止の切り替え
  const togglePlayPause = useCallback(async () => {
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
  }, [isPlaying, onPlay, onPause])

  // シーク処理
  const handleSeek = useCallback((value: number[]) => {
    if (!audioRef.current) return
    const newTime = value[0]
    if (newTime !== undefined) {
      audioRef.current.currentTime = newTime
      reader.updatePodcastTime(newTime)
    }
  }, [])

  // 音量変更
  const handleVolumeChange = useCallback((value: number) => {
    reader.setPodcastVolume(value)
  }, [])

  // 再生速度変更
  const handleSpeedChange = useCallback((speed: number) => {
    reader.setPodcastPlaybackRate(speed)
  }, [])

  // スキップ処理のヘルパー
  const seek = useCallback(
    (delta: number) => {
      if (!audioRef.current) return
      seekAudio(audioRef.current, delta, duration, (time) => {
        reader.updatePodcastTime(time)
      })
    },
    [duration],
  )

  // 10秒戻る
  const skipBack = useCallback(() => seek(-AUDIO_CONTROLS.SKIP_SECONDS), [seek])

  // 10秒進む
  const skipForward = useCallback(
    () => seek(AUDIO_CONTROLS.SKIP_SECONDS),
    [seek],
  )

  // プログレスバーのクリック処理
  const handleProgressClick = useCallback(
    (e: React.MouseEvent<HTMLDivElement>) => {
      if (!audioRef.current || !duration) return
      const rect = e.currentTarget.getBoundingClientRect()
      const x = e.clientX - rect.left
      const percentage = x / rect.width
      const newTime = percentage * duration
      handleSeek([newTime])
    },
    [duration, handleSeek],
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
      togglePlayPause,
      handleSeek,
      handleVolumeChange,
      handleSpeedChange,
      skipBack,
      skipForward,
      handleProgressClick,
    },
  }
}
