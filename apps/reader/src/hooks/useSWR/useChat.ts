import useSWR from 'swr'

import { components } from '../../lib/openapi-schema/schema'

import { fetcher } from './fetcher'

/**
 * ユーザーIDに紐づくチャット一覧を取得するSWRフック
 * @param userId ユーザーID (null の場合は fetch しない)
 */
export const useGetUserChats = (userId: string | null) => {
  // CR-3: 認証 user_id でサーバー側が絞り込むため、userId が null の場合のみ fetch をスキップ。
  const { data, error, isValidating, mutate } = useSWR<
    components['schemas']['ChatsResponse']
  >(userId ? `${process.env.NEXT_PUBLIC_API_BASE_URL}/chats/me` : null, fetcher)

  return {
    chats: data,
    error,
    isLoading: isValidating,
    mutateChats: mutate,
  }
}

/**
 * チャットIDに紐づくメッセージ一覧を取得するSWRフック
 * @param chatId チャットID (null の場合は fetch しない)
 */
export const useGetChatMessages = (chatId: string | null) => {
  const { data, error, isValidating, mutate } = useSWR<
    components['schemas']['MessageListResponse']
  >(
    chatId
      ? `${process.env.NEXT_PUBLIC_API_BASE_URL}/messages/${chatId}`
      : null,
    fetcher,
  )

  return {
    messages: data?.messages || [],
    error,
    isLoading: isValidating,
    mutateMessages: mutate,
  }
}
