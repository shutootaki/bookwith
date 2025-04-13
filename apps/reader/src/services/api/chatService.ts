import { ChatResponse, MessageResponse } from './types'

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000'

/**
 * チャットに関するAPIクライアント
 */
export const chatService = {
  /**
   * ユーザーIDに紐づくチャットをすべて取得する
   * @param userId ユーザーID
   * @returns チャット一覧
   */
  async getUserChats(userId: string): Promise<ChatResponse[]> {
    try {
      const response = await fetch(`${API_BASE_URL}/chats/user/${userId}`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      })

      if (!response.ok) {
        throw new Error(`Failed to fetch chats: ${response.statusText}`)
      }

      return await response.json()
    } catch (error) {
      console.error('Error fetching user chats:', error)
      throw error
    }
  },

  /**
   * チャットIDに紐づくメッセージをすべて取得する
   * @param chatId チャットID
   * @returns メッセージ一覧
   */
  async getChatMessages(chatId: string): Promise<MessageResponse[]> {
    try {
      const response = await fetch(`${API_BASE_URL}/messages/${chatId}`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      })

      if (!response.ok) {
        throw new Error(`Failed to fetch chat messages: ${response.statusText}`)
      }

      return (await response.json()).data
    } catch (error) {
      console.error('Error fetching chat messages:', error)
      throw error
    }
  },
}
