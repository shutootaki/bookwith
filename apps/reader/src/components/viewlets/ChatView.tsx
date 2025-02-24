// TODO: Chat履歴画面の作成

import { ArrowUpIcon, Check, Copy, Loader } from 'lucide-react'
import { useState, useEffect, useCallback, useRef } from 'react'
import React from 'react'

import { FormattedText } from '../FormattedText'
import { PaneViewProps } from '../base'
import { PaneView } from '../base'
import { Button } from '../ui/button'
import { Textarea } from '../ui/textarea'
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '../ui/tooltip'
interface Message {
  text: string
  sender: 'user' | 'assistant'
}

export const ChatView: React.FC<PaneViewProps> = (props) => {
  return (
    <PaneView {...props}>
      <ChatPane />
    </PaneView>
  )
}

interface ChatMessageProps {
  message: Message
}

const ChatMessage: React.FC<ChatMessageProps> = ({ message }) => {
  const [isCopied, setIsCopied] = useState(false)

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(message.text)
      setIsCopied(true)
      setTimeout(() => setIsCopied(false), 2000)
    } catch (err) {
      console.error('Failed to copy text:', err)
    }
  }

  return message.sender === 'user' ? (
    <div className="flex justify-end">
      <div className="max-w-[80%]">
        <div className="rounded-lg bg-[#424867] px-2 py-2 text-white">
          <FormattedText text={message.text} className="p-0 leading-relaxed" />
        </div>
      </div>
    </div>
  ) : (
    <div className="flex justify-start">
      <div>
        <div className="leading-relaxed">
          <FormattedText text={message.text} />
        </div>
        <Button
          variant="ghost"
          size="icon"
          className="h-6 w-6 text-gray-500 hover:text-gray-900"
          onClick={handleCopy}
        >
          {isCopied ? (
            <Check className="h-4 w-4" color="green" />
          ) : (
            <Copy className="h-4 w-4" />
          )}
        </Button>
      </div>
    </div>
  )
}
const EmptyState = () => (
  <div className="flex h-full flex-col justify-center px-2 text-center text-gray-500">
    <div className="mb-4">
      <svg
        className="mx-auto h-12 w-12"
        fill="none"
        stroke="currentColor"
        viewBox="0 0 24 24"
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={1.5}
          d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"
        />
      </svg>
    </div>
    <h3 className="text-lg font-medium">チャットを始めましょう</h3>
    <p className="text-sm">現在読書中の本の知識をもとにAIが回答します。</p>
  </div>
)

const useAutoResize = (
  text: string,
  textareaRef: React.RefObject<HTMLTextAreaElement>,
) => {
  useEffect(() => {
    const textarea = textareaRef.current
    if (!textarea) return
    textarea.style.height = 'auto'
    textarea.style.height = `${textarea.scrollHeight}px`
  }, [text, textareaRef])
}

const ChatPane: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([])
  const [text, setText] = useState('')
  const [isLoading, setIsLoading] = useState(false)

  const messagesEndRef = useRef<HTMLDivElement>(null)
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  const isEmpty = !text.trim()

  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [])

  useEffect(() => {
    scrollToBottom()
  }, [messages, scrollToBottom])

  useAutoResize(text, textareaRef)

  const handleSend = async (e: React.FormEvent | React.KeyboardEvent) => {
    e.preventDefault()
    if (isEmpty) return

    setMessages((prev) => [...prev, { sender: 'user', text }])
    setText('')
    setIsLoading(true)

    try {
      const response = await fetch('/api/llm', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question: text }),
      })

      if (!response.ok) throw new Error('APIリクエストに失敗しました')

      const data = await response.json()

      setMessages((prev) => [
        ...prev,
        { sender: 'assistant', text: data.answer || 'エラーが発生しました。' },
      ])
    } catch (error) {
      console.error('Error:', error)
      setMessages((prev) => [
        ...prev,
        { sender: 'assistant', text: 'エラーが発生しました。' },
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

      <div className="sticky bottom-0 border-t p-3">
        <form onSubmit={handleSend} className="flex w-full gap-1">
          <div className="bg-background w-full rounded-lg border p-2">
            <Textarea
              ref={textareaRef}
              value={text}
              onChange={(e) => setText(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) {
                  e.preventDefault()
                  handleSend(e)
                }
              }}
              placeholder="Type your message..."
              className="max-h-[300px] min-h-[30px] resize-none overflow-y-auto border-0 shadow-none focus-visible:ring-0"
              style={{ overflow: text ? 'auto' : 'hidden' }}
            />

            <div className="mt-2 flex items-center justify-end">
              <TooltipProvider delayDuration={200}>
                <Tooltip>
                  <TooltipTrigger asChild>
                    <Button
                      size="icon"
                      disabled={isEmpty}
                      className="h-6 w-6 rounded-full"
                    >
                      <ArrowUpIcon className="h-4 w-4" />
                    </Button>
                  </TooltipTrigger>
                  <TooltipContent>
                    `Cmd + Enter` or `Ctrl + Enter` で送信
                  </TooltipContent>
                </Tooltip>
              </TooltipProvider>
            </div>
          </div>
        </form>
      </div>
    </div>
  )
}
