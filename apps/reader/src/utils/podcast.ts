import { AlertCircle, Clock, Play, RefreshCw } from 'lucide-react'

import { SPEED_OPTIONS } from '../constants/audio'
import {
  PODCAST_STATUS_COLORS,
  PODCAST_STATUS_LABELS,
} from '../constants/podcast'
import { PodcastStatus } from '../types/podcast'

/**
 * ポッドキャスト状態に基づく色を取得
 */
export const getStatusColor = (status: string): string => {
  return (
    PODCAST_STATUS_COLORS[status as PodcastStatus] || 'text-gray-600 bg-gray-50'
  )
}

/**
 * ポッドキャスト状態に基づくアイコンを取得
 */
export const getStatusIcon = (status: string) => {
  switch (status) {
    case 'COMPLETED':
      return Play
    case 'PROCESSING':
      return RefreshCw
    case 'PENDING':
      return Clock
    case 'FAILED':
      return AlertCircle
    default:
      return Clock
  }
}

/**
 * ポッドキャスト状態に基づく翻訳キーを取得
 */
export const getStatusTextKey = (status: string): string => {
  return (
    PODCAST_STATUS_LABELS[status as PodcastStatus] || 'podcast.status.unknown'
  )
}

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
 * オーディオURLからファイル名を生成
 */
export const generateAudioFilename = (
  title: string,
  extension: string = '.mp3',
): string => {
  return `${title}${extension}`
}

/**
 * ポッドキャストの進捗を計算（処理中の場合）
 */
export const calculateProgress = (status: any): number | undefined => {
  if (!status) return undefined

  if (
    status.status === 'PROCESSING' &&
    status.script_turn_count &&
    status.script_character_count
  ) {
    // 実際の進捗計算ロジックはAPIの仕様に依存
    // ここでは例として undefined を返す
    return undefined
  }

  return undefined
}

/**
 * ポッドキャストタイトルを生成
 */
export const generatePodcastTitle = (bookName: string): string => {
  return `${bookName}のポッドキャスト`
}

/**
 * エラーメッセージをユーザーフレンドリーな形式に変換
 */
export const sanitizeErrorMessage = (error: string): string => {
  // APIから返される生のエラーメッセージを
  // ユーザーに表示可能な形式に変換
  return error.replace(/^Error:\s*/, '')
}

/**
 * ポッドキャストの状態が完了かどうかを判定
 */
export const isPodcastCompleted = (status: string): boolean => {
  return status === 'COMPLETED'
}

/**
 * ポッドキャストの状態が処理中かどうかを判定
 */
export const isPodcastProcessing = (status: string): boolean => {
  return status === 'PROCESSING'
}

/**
 * ポッドキャストの状態が失敗かどうかを判定
 */
export const isPodcastFailed = (status: string): boolean => {
  return status === 'FAILED'
}

/**
 * 配列から完了したポッドキャストを取得
 */
export const getCompletedPodcast = (podcasts: any[]): any | undefined => {
  return podcasts.find((p) => isPodcastCompleted(p.status))
}

/**
 * 配列から処理中のポッドキャストを取得
 */
export const getProcessingPodcast = (podcasts: any[]): any | undefined => {
  return podcasts.find((p) => isPodcastProcessing(p.status))
}

/**
 * ブラウザがWeb Share APIをサポートしているかチェック
 */
export const isWebShareSupported = (): boolean => {
  return typeof navigator !== 'undefined' && 'share' in navigator
}

/**
 * クリップボードAPIがサポートされているかチェック
 */
export const isClipboardSupported = (): boolean => {
  return typeof navigator !== 'undefined' && 'clipboard' in navigator
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
 * ポッドキャストに利用可能な音声URLがあるかチェック
 */
export const hasAudioUrl = (podcast: any): boolean => {
  return !!(podcast.audio_url && podcast.audio_url.trim())
}
