export interface Message {
  text: string
  sender_type: 'user' | 'assistant'
}

export interface TextAreaRefType {
  current: HTMLTextAreaElement | null
}
