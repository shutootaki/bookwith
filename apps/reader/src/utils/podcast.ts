import { SPEED_OPTIONS } from '../constants/audio'
import { PODCAST_ERROR_KEYS, PODCAST_STATUS_PRIORITY } from '../constants/podcast'
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
 * 日付を日本語形式でフォーマット
 */
export const formatDate = (dateString: string): string => {
  return new Date(dateString).toLocaleString('ja-JP')
}

/**
 * 日付を日付のみの形式でフォーマット
 */
export const formatDateOnly = (dateString: string): string => {
  return new Date(dateString).toLocaleDateString('ja-JP')
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
 * 優先順位に基づいてポッドキャストを選択
 */
export const selectPodcastByPriority = (
  podcasts: PodcastResponse[],
): PodcastResponse | null => {
  for (const status of PODCAST_STATUS_PRIORITY) {
    const podcast = findPodcastByStatus(podcasts, status)
    if (podcast) {
      return podcast
    }
  }
  return null
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

/**
 * ポッドキャストが再生可能かどうかを判定
 */
export const isPodcastPlayable = (podcast: PodcastResponse): boolean => {
  return podcast.status === 'COMPLETED' && !!podcast.audio_url
}

/**
 * ポッドキャストのタイトルをフォーマット
 */
export const formatPodcastTitle = (
  title: string,
  maxLength?: number,
): string => {
  if (!maxLength || title.length <= maxLength) {
    return title
  }
  return `${title.substring(0, maxLength - 3)}...`
}

/**
 * ポッドキャストの継続時間をフォーマット
 */
export const formatDuration = (seconds: number): string => {
  if (isNaN(seconds)) return '--:--'
  const hours = Math.floor(seconds / 3600)
  const minutes = Math.floor((seconds % 3600) / 60)
  const secs = Math.floor(seconds % 60)
  
  if (hours > 0) {
    return `${hours}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
  }
  return formatTime(seconds)
}
