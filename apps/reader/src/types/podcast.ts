import { components } from '../lib/openapi-schema/schema'

// OpenAPI schema から型を再エクスポート
export type PodcastResponse = components['schemas']['PodcastResponse']
export type CreatePodcastRequest = components['schemas']['CreatePodcastRequest']
export type CreatePodcastResponse =
  components['schemas']['CreatePodcastResponse']
export type PodcastListResponse = components['schemas']['PodcastListResponse']
export type PodcastStatusResponse =
  components['schemas']['PodcastStatusResponse']

// ポッドキャスト状態の型定義
export type PodcastStatus = 'PENDING' | 'PROCESSING' | 'COMPLETED' | 'FAILED'

// 再生速度オプションの型定義
export interface SpeedOption {
  value: number
  label: string
}
