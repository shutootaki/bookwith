import React, { useCallback, useEffect, useRef } from 'react'
import { Loader } from 'lucide-react'
import { useReaderSnapshot } from '../../../models'
import { ChatMessage } from './ChatMessage'
import { ChatInputForm } from './ChatInputForm'
import { EmptyState } from './EmptyState'
import { Message } from './types'
import { useTranslation } from '@flow/reader/hooks'

interface ChatPaneProps {
  messages: Message[]
  setMessages: React.Dispatch<React.SetStateAction<Message[]>>
  text: string
  setText: React.Dispatch<React.SetStateAction<string>>
  isLoading: boolean
  setIsLoading: React.Dispatch<React.SetStateAction<boolean>>
}

export const ChatPane: React.FC<ChatPaneProps> = ({
  messages,
  setMessages,
  text,
  setText,
  isLoading,
  setIsLoading,
}) => {
  const { focusedTab } = useReaderSnapshot()
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const t = useTranslation()

  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [])

  useEffect(() => {
    scrollToBottom()
  }, [messages, scrollToBottom])

  const handleSend = async (e: React.FormEvent | React.KeyboardEvent) => {
    e.preventDefault()
    if (!text.trim() || isLoading) return

    setMessages((prev) => [...prev, { sender_type: 'user', text }])
    setText('')
    setIsLoading(true)

    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_BASE_URL}/message`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            question: text,
            tenant_id: focusedTab
              ? `test_user_id_${focusedTab?.id}`
              : undefined,
          }),
        },
      )

      if (!response.ok) throw new Error(t('chat.error'))

      const data = await response.json()

      setMessages((prev) => [
        ...prev,
        { sender_type: 'assistant', text: data.answer || t('chat.error') },
      ])
    } catch (error) {
      console.error('Error:', error)
      setMessages((prev) => [
        ...prev,
        { sender_type: 'assistant', text: t('chat.error') },
      ])
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="mx-auto flex h-full w-full max-w-4xl flex-col">
      {messages.length === 0 ? (
        <EmptyState />
      ) : (
        <div className="flex-1 space-y-2 overflow-y-auto p-4 text-sm">
          {messages.map((msg, index) => (
            <ChatMessage key={index} message={msg} />
          ))}
          {isLoading && (
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
