import { SPEED_OPTIONS } from '../constants/audio'
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
