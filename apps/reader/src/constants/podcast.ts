import { PodcastStatus } from '../types/podcast'

// ポッドキャスト状態の色分けマッピング
export const PODCAST_STATUS_COLORS = {
  COMPLETED: 'text-green-600 bg-green-50',
  PROCESSING: 'text-blue-600 bg-blue-50',
  PENDING: 'text-yellow-600 bg-yellow-50',
  FAILED: 'text-red-600 bg-red-50',
} as const

// ポッドキャスト状態の日本語表示名
export const PODCAST_STATUS_LABELS = {
  COMPLETED: 'podcast.status.completed',
  PROCESSING: 'podcast.status.processing',
  PENDING: 'podcast.status.pending',
  FAILED: 'podcast.status.failed',
} as const

// ポッドキャストの状態優先順位
export const PODCAST_STATUS_PRIORITY: PodcastStatus[] = [
  'COMPLETED',
  'PROCESSING',
  'FAILED',
  'PENDING',
]

// ポーリング関連の定数
export const POLLING_CONFIG = {
  INTERVAL: 2000, // 2秒間隔
  TIMEOUT: 300000, // 5分間のタイムアウト
} as const

// ポッドキャスト生成関連の定数
export const PODCAST_GENERATION = {
  MAX_RETRY_ATTEMPTS: 3,
  TITLE_SUFFIX: 'のポッドキャスト',
} as const

// エラーメッセージのキー
export const PODCAST_ERROR_KEYS = {
  GENERATION_FAILED: 'podcast.pane.generation_failed',
  REGENERATION_FAILED: 'podcast.pane.regeneration_failed',
  LOADING_FAILED: 'podcast.pane.loading_failed',
  PLAYBACK_FAILED: 'podcast.audio_player.playback_failed',
  NETWORK_ERROR: 'podcast.errors.network_error',
  UNKNOWN_ERROR: 'podcast.errors.unknown',
} as const

// ポッドキャスト関連のデフォルト値
export const PODCAST_DEFAULTS = {
  VOLUME: 1.0,
  PLAYBACK_RATE: 1.0,
  CURRENT_TIME: 0,
  DURATION: 0,
} as const

// ファイル関連の定数
export const PODCAST_FILE = {
  AUDIO_EXTENSION: '.mp3',
  MIME_TYPE: 'audio/mpeg',
  DOWNLOAD_PREFIX: 'podcast_',
} as const

// ポッドキャストのアイコンサイズ
export const PODCAST_ICON_SIZES = {
  XS: 'h-3 w-3',
  SM: 'h-4 w-4',
  MD: 'h-6 w-6',
  LG: 'h-8 w-8',
} as const

// キーボードショートカット
export const PODCAST_KEYBOARD_SHORTCUTS = {
  PLAY_PAUSE: ' ',
  SKIP_FORWARD: 'ArrowRight',
  SKIP_BACK: 'ArrowLeft',
  VOLUME_UP: 'ArrowUp',
  VOLUME_DOWN: 'ArrowDown',
  SPEED_UP: '>',
  SPEED_DOWN: '<',
  MUTE_TOGGLE: 'm',
} as const

// UIコンポーネントのクラス名
export const PODCAST_UI_CLASSES = {
  ERROR_CARD: 'rounded-md border border-red-200 bg-red-50 p-3',
  PROCESSING_CARD: 'border-blue-200 bg-blue-50 p-6',
  FAILED_CARD: 'border-destructive/50 bg-destructive/5 p-6',
  CONTROL_BUTTON: 'h-8 w-8',
  PLAY_BUTTON: 'h-12 w-12',
} as const

// アニメーションクラス
export const PODCAST_ANIMATIONS = {
  SPIN: 'animate-spin',
  FADE_IN: 'animate-fade-in',
  FADE_OUT: 'animate-fade-out',
} as const
