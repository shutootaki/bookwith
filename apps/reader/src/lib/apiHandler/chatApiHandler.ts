import { components } from '../openapi-schema/schema'

import { apiClient } from './apiClient'

type ChatsResponse = components['schemas']['ChatsResponse']
type MessageListResponse = components['schemas']['MessageListResponse']

/**
 * Fetches all chats for a specific user using the apiClient.
 * @param userId The ID of the user whose chats are to be fetched.
 * @returns A promise that resolves to ChatsResponse.
 * @throws Throws an error if the API request fails.
 */
export const getUserChats = async (userId: string): Promise<ChatsResponse> => {
  try {
    const responseData = await apiClient<ChatsResponse>(
      `/chats/user/${userId}`,
      { method: 'GET' },
    )
    return responseData
  } catch (error) {
    console.error(`Error fetching user chats for user ${userId}:`, error)
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
