import { components } from '../lib/openapi-schema/schema'

export type PodcastResponse = components['schemas']['PodcastResponse']

export type PodcastStatus = 'PENDING' | 'PROCESSING' | 'COMPLETED' | 'FAILED'
