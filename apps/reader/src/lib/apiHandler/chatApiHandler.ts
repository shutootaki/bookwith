import { components } from '../openapi-schema/schema'

import { apiClient } from './apiClient'

type ChatsResponse = components['schemas']['ChatsResponse']
type MessageListResponse = components['schemas']['MessageListResponse']

/**
 * Fetches all chats for the authenticated user.
 * @returns A promise that resolves to ChatsResponse.
 * @throws Throws an error if the API request fails.
 */
export const getUserChats = async (): Promise<ChatsResponse> => {
  try {
    const responseData = await apiClient<ChatsResponse>(`/chats/me`, {
      method: 'GET',
    })
    return responseData
  } catch (error) {
    console.error(`Error fetching authenticated user chats:`, error)
    throw error
  }
}

/**
 * Fetches all messages for a specific chat using the apiClient.
 * @param chatId The ID of the chat whose messages are to be fetched.
 * @returns A promise that resolves to MessageListResponse.
 * @throws Throws an error if the API request fails.
 */
export const getChatMessages = async (
  chatId: string,
): Promise<MessageListResponse> => {
  try {
    const responseData = await apiClient<MessageListResponse>(
      `/messages/${chatId}`,
      { method: 'GET' },
    )
    return responseData
  } catch (error) {
    console.error(`Error fetching messages for chat ${chatId}:`, error)
    throw error
  }
}
