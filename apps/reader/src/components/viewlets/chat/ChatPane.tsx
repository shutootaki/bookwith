import { Loader } from 'lucide-react'
import React, { useCallback, useEffect, useRef } from 'react'
import { v4 as uuidv4 } from 'uuid'

import { useTranslation } from '@flow/reader/hooks'

import { useReaderSnapshot } from '../../../models'
import { TEST_USER_ID } from '../../../pages/_app'

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
      {messages.length === 0 ? (
        <EmptyState />
      ) : (
        <div className="flex-1 space-y-2 overflow-y-auto p-4 text-sm">
          {messages.map((msg, index) => (
            <ChatMessage key={index} message={msg} />
          ))}
          {isLoading && messages[messages.length - 1]?.text === '' && (
            <Loader className="flex h-4 w-4 animate-spin justify-start" />
          )}
          <div ref={messagesEndRef} />
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
