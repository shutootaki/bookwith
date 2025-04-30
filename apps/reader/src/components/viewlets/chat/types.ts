import { components } from '../../../lib/openapi-schema/schema'

export interface Message {
  text: string
  senderType: components['schemas']['SenderTypeEnum']
}

export interface TextAreaRefType {
  current: HTMLTextAreaElement | null
}
