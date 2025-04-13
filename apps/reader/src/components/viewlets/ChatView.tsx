import React, { useState } from 'react'
import { History, PlusCircle } from 'lucide-react'
import { PaneViewProps, PaneView } from '../base'
import { useTranslation } from '@flow/reader/hooks'

import { ChatHistoryCommandDialog } from './chat/ChatHistoryCommandDialog'
import { ChatPane } from './chat/ChatPane'
import { Message } from './chat/types'
import { chatService } from '../../services/api/chatService'
import { MessageResponse } from '../../services/api/types'

export const ChatView: React.FC<PaneViewProps> = (props) => {
  const [messages, setMessages] = useState<Message[]>([])
  const [text, setText] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [showHistory, setShowHistory] = useState(false)
  const [selectedChatId, setSelectedChatId] = useState<string | null>(null)
  const t = useTranslation()

  const resetChat = () => {
    setMessages([])
    setText('')
    setIsLoading(false)
    setSelectedChatId(null)
  }

  const handleSelectChat = async (chatId: string) => {
    try {
      setIsLoading(true)
      setSelectedChatId(chatId)

      const chatMessages = await chatService.getChatMessages(chatId)

      const uiMessages = chatMessages.map((msg: MessageResponse) => ({
        text: msg.content,
        sender_type: msg.sender_type,
      }))

      setMessages(uiMessages)
      setShowHistory(false)
    } catch (error) {
      console.error('Failed to load chat:', error)
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <PaneView
      actions={[
        {
          id: 'history',
          Icon: History,
          title: t('chat.history'),
          handle: () => setShowHistory(true),
        },
        {
          id: 'new-chat',
          Icon: PlusCircle,
          title: t('chat.new'),
          handle: resetChat,
        },
      ]}
      {...props}
    >
      <ChatPane
        messages={messages}
        setMessages={setMessages}
        text={text}
        setText={setText}
        isLoading={isLoading}
        setIsLoading={setIsLoading}
        chatId={selectedChatId}
      />

      <ChatHistoryCommandDialog
        open={showHistory}
        onOpenChange={setShowHistory}
        onSelectChat={handleSelectChat}
      />
    </PaneView>
  )
}
