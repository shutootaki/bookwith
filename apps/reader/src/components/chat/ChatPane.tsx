import { Loader, BookOpen } from 'lucide-react'
import React, { useCallback, useEffect, useRef, useState } from 'react'
import { v4 as uuidv4 } from 'uuid'

import { useTranslation } from '@flow/reader/hooks'

import { apiClient } from '../../lib/apiHandler/apiClient'
import { components } from '../../lib/openapi-schema/schema'
import { useReaderSnapshot } from '../../models'
import { TEST_USER_ID } from '../../pages/_app'
import { ResponsiveToolTip } from '../ResponsiveToolTip'

import { BookInfoTooltipContent } from './BookInfoTooltipContent'
import { ChatInputForm } from './ChatInputForm'
import { ChatMessage } from './ChatMessage'
import { EmptyState } from './EmptyState'
import { Message } from './types'

interface ChatPaneProps {
  messages: Message[]
  setMessages: React.Dispatch<React.SetStateAction<Message[]>>
  text: string
  setText: React.Dispatch<React.SetStateAction<string>>
  isLoading: boolean
  setIsLoading: React.Dispatch<React.SetStateAction<boolean>>
  chatId?: string | null
}

type ChatResponse = components['schemas']['ChatResponse']

export const ChatPane: React.FC<ChatPaneProps> = ({
  messages,
  setMessages,
  text,
  setText,
  isLoading,
  setIsLoading,
  chatId,
}) => {
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const t = useTranslation()
  const { focusedBookTab } = useReaderSnapshot()
  const [chatTitle, setChatTitle] = useState<string | null>(null)
  useEffect(() => {
    setChatTitle(null)
  }, [chatId])
  const bookTitle =
    focusedBookTab?.book.metadataTitle ?? focusedBookTab?.book.name

  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [])

  const updateAssistantMessage = useCallback(
    (content: string) => {
      setMessages((prev) => {
        const messagesSnapshot = [...prev]
        const lastMessage = messagesSnapshot[messagesSnapshot.length - 1]
        if (lastMessage?.senderType === 'assistant') {
          lastMessage.text = content
        }
        return messagesSnapshot
      })
    },
    [setMessages],
  )

  useEffect(() => {
    scrollToBottom()
  }, [messages, scrollToBottom])

  // チャットがまだ DB に保存される前 (POST /messages 直後) は 404 になる可能性がある。
  // 404 が返った場合は指数バックオフ付きで最大 5 回リトライする。
  useEffect(() => {
    if (!chatId || isLoading || messages.length === 0) return

    let cancelled = false

    ;(async () => {
      for (let retry = 0; retry < 5; retry++) {
        try {
          const res = await apiClient<ChatResponse>(`/chats/${chatId}`)
          if (res.title && !cancelled) setChatTitle(res.title)
          return
        } catch (err) {
          const isNotFound =
            err instanceof Error &&
            err.message.includes('チャットが見つかりません')
          if (!isNotFound) {
            console.error('Failed to fetch chat title:', err)
            return
          }
          await new Promise((r) => setTimeout(r, 2 ** retry * 300))
        }
      }
    })()

    return () => {
      cancelled = true
    }
  }, [chatId, isLoading, messages.length])

  const processStream = useCallback(
    async (stream: ReadableStream) => {
      const reader = stream.getReader()
      const decoder = new TextDecoder()
      let accumulatedContent = ''

      try {
        while (true) {
          const { done, value } = await reader.read()
          if (done) break

          const chunk = decoder.decode(value, { stream: true })
          accumulatedContent += chunk

          updateAssistantMessage(accumulatedContent)
          scrollToBottom()
        }
      } catch (error) {
        console.error('Stream processing error:', error)
        throw error
      }
    },
    [scrollToBottom, updateAssistantMessage],
  )

  const handleSend = useCallback(
    async (e: React.FormEvent | React.KeyboardEvent) => {
      e.preventDefault()
      if (!text.trim() || isLoading) return

      const trimmedText = text.trim()

      setMessages((prev) => [
        ...prev,
        { senderType: 'user', text: trimmedText },
      ])
      setText('')
      setIsLoading(true)

      setMessages((prev) => [...prev, { senderType: 'assistant', text: '' }])

      try {
        const response = await fetch(
          `${process.env.NEXT_PUBLIC_API_BASE_URL}/messages`,
          {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              content: trimmedText,
              chat_id: chatId || uuidv4(),
              sender_id: TEST_USER_ID,
              book_id: focusedBookTab?.book.id,
              metadata: {},
            }),
          },
        )

        if (!response.ok || !response.body) throw new Error(t('chat.error'))

        await processStream(response.body)
      } catch {
        updateAssistantMessage(t('chat.error'))
      } finally {
        setIsLoading(false)
      }
    },
    [
      text,
      isLoading,
      chatId,
      focusedBookTab,
      t,
      updateAssistantMessage,
      setMessages,
      setText,
      setIsLoading,
      processStream,
    ],
  )

  return (
    <div className="mx-auto flex h-full w-full max-w-4xl flex-col">
      {(messages.length > 0 || focusedBookTab) && (
        <div className="border-b border-gray-200 px-4 pb-3 dark:border-gray-700">
          <div className="flex flex-col gap-1.5">
            {messages.length > 0 && chatTitle && (
              <h3
                className="flex-1 truncate text-xs font-semibold"
                title={chatTitle}
              >
                {chatTitle}
              </h3>
            )}
            {focusedBookTab && (
              <ResponsiveToolTip
                content={
                  <BookInfoTooltipContent
                    title={bookTitle ?? ''}
                    author={focusedBookTab.book.author}
                    pubdate={focusedBookTab.book.metadataPubdate}
                    percentage={focusedBookTab.book.percentage}
                  />
                }
              >
                <span className="flex items-center text-xs text-gray-600 dark:text-gray-400">
                  <BookOpen className="mr-1 h-4 w-4 shrink-0" />
                  <span className="truncate  font-medium">
                    {bookTitle ?? ''}
                  </span>
                </span>
              </ResponsiveToolTip>
            )}
          </div>
        </div>
      )}

      {messages.length === 0 ? (
        <EmptyState />
      ) : (
        <div className="flex-1 overflow-y-auto">
          <div className="space-y-2 p-4 text-sm">
            {messages.map((msg, index) => (
              <ChatMessage key={index} message={msg} />
            ))}
            {isLoading && messages[messages.length - 1]?.text === '' && (
              <div className="flex items-center gap-2 text-gray-500 dark:text-gray-400">
                <Loader className="h-4 w-4 animate-spin" />
                <span className="animate-pulse text-sm">
                  {t('chat.generating')}
                </span>
              </div>
            )}
            <div ref={messagesEndRef} className="h-4" />
          </div>
        </div>
      )}

      <ChatInputForm
        text={text}
        setText={setText}
        onSend={handleSend}
        isLoading={isLoading}
      />
    </div>
  )
}
