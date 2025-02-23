import { ArrowUpIcon, Copy, Loader } from 'lucide-react'
import { useState, useEffect, useCallback } from 'react'
import React from 'react'

import { PaneViewProps } from '../base'
import { PaneView } from '../base'
import { Button } from '../ui/button'
import { Textarea } from '../ui/textarea'

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

const ChatPane: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([])
  const [text, setText] = useState('')
  const messagesEndRef = React.useRef<HTMLDivElement>(null)
  const [isLoading, setIsLoading] = React.useState(false)
  const textareaRef = React.useRef<HTMLTextAreaElement>(null)
  const is_empty = !text.trim()

  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [])

  // メッセージが追加されたときに自動スクロール
  useEffect(() => {
    scrollToBottom()
  }, [messages, scrollToBottom])

  // Adjust height when text changes
  useEffect(() => {
    const textarea = textareaRef.current
    if (!textarea) return

    textarea.style.height = 'auto'
    textarea.style.height = `${textarea.scrollHeight}px`
  }, [text])

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault()
    if (is_empty) return

    setMessages((prev) => [
      ...prev,
      {
        sender: 'user',
        text: text,
      },
    ])
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
        {
          text: data.answer || 'エラーが発生しました。',
          sender: 'assistant',
        },
      ])
    } catch (error) {
      console.error('Error:', error)
      setMessages((prev) => [
        ...prev,
        {
          text: 'エラーが発生しました。',
          sender: 'assistant',
        },
      ])
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="flex h-full w-full max-w-2xl flex-col">
      <div className="flex-1 space-y-2 overflow-y-auto p-4 text-sm">
        {messages.map((message, i) => (
          <div
            key={i}
            className={`flex ${
              message.sender === 'user' ? 'justify-end' : 'justify-start'
            }`}
          >
            {message.sender === 'user' ? (
              <div className="max-w-[80%]">
                <div className="rounded-lg bg-[#424867] px-2 py-2 text-white">
                  <div className="leading-relaxed">{message.text}</div>
                </div>
              </div>
            ) : (
              <div>
                <div className="leading-relaxed">{message.text}</div>
                <div className="mt-1 flex gap-2">
                  <Button
                    variant="ghost"
                    size="icon"
                    className="h-6 w-6 text-gray-500 hover:text-gray-900"
                  >
                    <Copy className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            )}
          </div>
        ))}
        {isLoading && (
          <Loader className="flex h-4 w-4 animate-spin justify-start" />
        )}
        <div ref={messagesEndRef} />
      </div>

      <div className="sticky bottom-0 border-t p-3">
        <form onSubmit={handleSend} className="flex w-full gap-1">
          <div className="bg-background w-full max-w-2xl rounded-lg border p-2">
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
              <Button
                size="icon"
                disabled={is_empty}
                className="h-6 w-6 rounded-full bg-black text-white hover:bg-black/90"
              >
                <ArrowUpIcon className="h-4 w-4" />
              </Button>
            </div>
          </div>
        </form>
      </div>
    </div>
  )
}
