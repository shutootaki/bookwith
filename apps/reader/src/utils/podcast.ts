import { SPEED_OPTIONS } from '../constants/audio'
import { PODCAST_ERROR_KEYS } from '../constants/podcast'
import { PodcastResponse, PodcastStatus } from '../types/podcast'

/**
 * 時間をMM:SS形式でフォーマット
 */
export const formatTime = (time: number): string => {
  if (isNaN(time)) return '0:00'
  const minutes = Math.floor(time / 60)
  const seconds = Math.floor(time % 60)
  return `${minutes}:${seconds.toString().padStart(2, '0')}`
}

/**
 * 再生速度オプションから指定された値のラベルを取得
 */
export const getSpeedLabel = (playbackRate: number): string => {
  const option = SPEED_OPTIONS.find((opt) => opt.value === playbackRate)
  return option?.label || '1x'
}

/**
 * 音量をパーセンテージでフォーマット
 */
export const formatVolumePercentage = (volume: number): string => {
  return `${Math.round(volume * 100)}%`
}

/**
 * オーディオの現在位置をシーク
 */
export const seekAudio = (
  audioElement: HTMLAudioElement,
  delta: number,
  duration: number,
  onTimeUpdate: (time: number) => void,
): void => {
  const newTime = Math.min(
    Math.max(0, audioElement.currentTime + delta),
    duration,
  )
  audioElement.currentTime = newTime
  onTimeUpdate(newTime)
}

/**
 * 配列から指定した状態のポッドキャストを取得
 */
export const findPodcastByStatus = (
  podcasts: PodcastResponse[],
  status: PodcastStatus,
): PodcastResponse | undefined => {
  return podcasts.find((p) => p.status === status)
}

/**
 * エラータイプに基づいてエラーメッセージキーを取得
 */
export const getPodcastErrorKey = (error: unknown): string => {
  if (error instanceof Error) {
    if (error.message.includes('network')) {
      return PODCAST_ERROR_KEYS.NETWORK_ERROR
    }
    if (error.message.includes('audio') || error.message.includes('play')) {
      return PODCAST_ERROR_KEYS.PLAYBACK_FAILED
    }
    if (error.message.includes('generation')) {
      return PODCAST_ERROR_KEYS.GENERATION_FAILED
    }
  }
  return PODCAST_ERROR_KEYS.UNKNOWN_ERROR
}
