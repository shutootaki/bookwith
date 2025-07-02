import { components } from '../../../lib/openapi-schema/schema'

export interface Message {
  text: components['schemas']['MessageResponse']['content']
  senderType: components['schemas']['MessageResponse']['senderType']
}
