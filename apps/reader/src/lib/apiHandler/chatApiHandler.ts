import { components } from '../openapi-schema/schema'

export const getUserChats = async (
  userId: string,
): Promise<components['schemas']['ChatsResponse']> => {
  try {
    const response = await fetch(
      `${process.env.NEXT_PUBLIC_API_BASE_URL}/chats/user/${userId}`,
      {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      },
    )

    if (!response.ok) {
      throw new Error(`Failed to fetch chats: ${response.statusText}`)
    }

    return await response.json()
  } catch (error) {
    console.error('Error fetching user chats:', error)
    throw error
  }
}

export const getChatMessages = async (
  chatId: string,
): Promise<components['schemas']['MessageListResponse']> => {
  try {
    const response = await fetch(
      `${process.env.NEXT_PUBLIC_API_BASE_URL}/messages/${chatId}`,
      {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      },
    )

    if (!response.ok) {
      throw new Error(`Failed to fetch chat messages: ${response.statusText}`)
    }

    return (await response.json()).data
  } catch (error) {
    console.error('Error fetching chat messages:', error)
    throw error
  }
}
