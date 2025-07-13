// エラーメッセージのキー
export const PODCAST_ERROR_KEYS = {
  GENERATION_FAILED: 'podcast.pane.generation_failed',
  REGENERATION_FAILED: 'podcast.pane.regeneration_failed',
  LOADING_FAILED: 'podcast.pane.loading_failed',
  PLAYBACK_FAILED: 'podcast.audio_player.playback_failed',
  NETWORK_ERROR: 'podcast.errors.network_error',
  UNKNOWN_ERROR: 'podcast.errors.unknown',
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
