import { Loader2, ArrowUpIcon } from 'lucide-react'
import * as React from 'react'
import { useCallback } from 'react'
import { useEffect } from 'react'

import { cn } from '../../lib/utils'
import { Button } from '../ui/button'
import { Card, CardContent, CardFooter } from '../ui/card'
import { ScrollArea } from '../ui/scroll-area'
import { Textarea } from '../ui/textarea'

interface Message {
  text: string
  sender: string
  timestamp?: Date
}

const ChatMessage = ({ message }: { message: Message }) => {
  const isUser = message.sender === 'user'

  return (
    <div
      className={cn(
        'mb-4 flex w-max max-w-[80%] items-end gap-2',
        isUser ? 'ml-auto' : 'mr-auto',
      )}
    >
      <div
        className={cn(
          'rounded-lg px-4 py-2 text-sm',
          isUser ? 'bg-primary text-primary-foreground' : 'bg-muted',
        )}
      >
        <p className="whitespace-pre-wrap break-words">{message.text}</p>
      </div>
    </div>
  )
}

interface ChatViewProps {
  className?: string
  title?: string
}

export function ChatView({ className, title = 'Chat' }: ChatViewProps) {
  const [messages, setMessages] = React.useState<Message[]>([])
  const [isLoading, setIsLoading] = React.useState(false)
  const scrollRef = React.useRef<HTMLDivElement>(null)
  const [text, setText] = React.useState('')
  const textareaRef = React.useRef<HTMLTextAreaElement>(null)

  const scrollToBottom = React.useCallback(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollIntoView({ behavior: 'smooth' })
    }
  }, [])

  const adjustHeight = useCallback(() => {
    const textarea = textareaRef.current
    if (textarea) {
      // Reset height to auto to get the correct scrollHeight
      textarea.style.height = 'auto'
      // Set the height to match the content
      textarea.style.height = `${textarea.scrollHeight}px`
    }
  }, [])

  // Adjust height when text changes
  useEffect(() => {
    adjustHeight()
  }, [adjustHeight, text])

  React.useEffect(() => {
    scrollToBottom()
  }, [scrollToBottom])

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault()

    if (!text.trim()) return

    const userMessage = {
      text: text,
      sender: 'user',
      timestamp: new Date(),
    }

    setMessages((prev) => [...prev, userMessage])
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
          sender: 'bot',
          timestamp: new Date(),
        },
      ])
    } catch (error) {
      console.error('Error:', error)
      setMessages((prev) => [
        ...prev,
        {
          text: 'エラーが発生しました。',
          sender: 'bot',
          timestamp: new Date(),
        },
      ])
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <Card
      className={cn('flex h-full flex-col border-none shadow-none', className)}
    >
      <div className="p-4">{title}</div>
      <CardContent className="flex-1 p-4">
        <ScrollArea className="h-full pr-4">
          <div className="space-y-4">
            {messages.map((message, i) => (
              <ChatMessage key={i} message={message} />
            ))}
            {isLoading && (
              <div className="text-muted-foreground flex items-center gap-2">
                <Loader2 className="h-4 w-4 animate-spin" />
                <p className="text-sm">入力中...</p>
              </div>
            )}
            <div ref={scrollRef} />
          </div>
        </ScrollArea>
      </CardContent>
      <CardFooter className="border-t py-4 px-2">
        <form onSubmit={handleSend} className="flex w-full gap-1">
          <div className="bg-background w-full max-w-2xl rounded-lg border p-1">
            <Textarea
              ref={textareaRef}
              value={text}
              onChange={(e) => setText(e.target.value)}
              placeholder="Type your message..."
              className="max-h-[300px] min-h-[30px] resize-none overflow-y-auto border-0 shadow-none focus-visible:ring-0"
              style={{ overflow: text ? 'auto' : 'hidden' }}
            />
            <div className="mt-2 flex items-center justify-end">
              <Button
                size="icon"
                className="h-6 w-6 rounded-full bg-black text-white hover:bg-black/90"
              >
                <ArrowUpIcon className="h-4 w-4" />
              </Button>
            </div>
          </div>
        </form>
      </CardFooter>
    </Card>
  )
}
