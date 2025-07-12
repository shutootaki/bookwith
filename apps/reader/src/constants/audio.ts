import { SpeedOption } from '../types/podcast'

// オーディオ制御関連の定数
export const AUDIO_CONTROLS = {
  SKIP_SECONDS: 10, // スキップする秒数
  VOLUME_STEP: 0.1, // 音量調整のステップ
  DEFAULT_VOLUME: 1.0, // デフォルト音量
  MIN_VOLUME: 0, // 最小音量
  MAX_VOLUME: 1, // 最大音量
} as const

// 長押し関連の定数
export const LONG_PRESS = {
  DEFAULT_INTERVAL: 200, // 長押し時の間隔（ミリ秒）
  INITIAL_DELAY: 500, // 長押し判定の遅延（ミリ秒）
} as const

// 再生速度オプション
export const SPEED_OPTIONS: SpeedOption[] = [
  { value: 0.5, label: '0.5x' },
  { value: 0.75, label: '0.75x' },
  { value: 1, label: '1x' },
  { value: 1.25, label: '1.25x' },
  { value: 1.5, label: '1.5x' },
  { value: 2, label: '2x' },
]

// デフォルト再生速度
export const DEFAULT_PLAYBACK_RATE = 1.0

// オーディオ関連のキー定数
export const AUDIO_EVENTS = {
  TIME_UPDATE: 'timeupdate',
  LOADED_METADATA: 'loadedmetadata',
  ENDED: 'ended',
  LOAD_START: 'loadstart',
  CAN_PLAY: 'canplay',
  ERROR: 'error',
} as const

// 音量スライダー関連の定数
export const VOLUME_SLIDER = {
  MIN: 0,
  MAX: 1,
  STEP: 0.1,
} as const

// オーディオファイル関連の定数
export const AUDIO_FILE = {
  PRELOAD: 'metadata' as const,
  CROSSORIGIN: 'anonymous' as const,
}

// オーディオ状態の定数
export const AUDIO_STATE = {
  LOADING: 'loading',
  PLAYING: 'playing',
  PAUSED: 'paused',
  ENDED: 'ended',
  ERROR: 'error',
} as const

// フォーマット関連の定数
export const TIME_FORMAT = {
  INVALID_TIME: '0:00',
  PAD_START_LENGTH: 2,
  PAD_CHAR: '0',
} as const
