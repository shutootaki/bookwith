/**
 * チャットレスポンスの型定義
 */
export interface ChatResponse {
  id: string
  user_id: string
  title: string | null
  book_id: string | null
  created_at: string
  updated_at: string
}

/**
 * メッセージレスポンスの型定義
 */
export interface MessageResponse {
  id: string
  chat_id: string
  sender_id: string
  sender_type: 'user' | 'assistant'
  content: string
  metadata: Record<string, any>
  created_at: string
  updated_at: string
}
