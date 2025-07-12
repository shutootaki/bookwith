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
} as const
