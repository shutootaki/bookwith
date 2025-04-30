import { History, PlusCircle } from 'lucide-react'
import React, { useState, useEffect } from 'react'
import { v4 as uuidv4 } from 'uuid'

import { useTranslation } from '@flow/reader/hooks'

import { useIntermediateChatKeyword } from '../../hooks/useIntermediateChatKeyword'
import { getChatMessages } from '../../lib/apiHandler/chatApiHandler'
import { PaneViewProps, PaneView } from '../base'

import { ChatHistoryCommandDialog } from './chat/ChatHistoryCommandDialog'
import { ChatPane } from './chat/ChatPane'
import { Message } from './chat/types'

export const ChatView: React.FC<PaneViewProps> = (props) => {
  const [messages, setMessages] = useState<Message[]>([])
  const [text, setText] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [showHistory, setShowHistory] = useState(false)
  const [selectedChatId, setSelectedChatId] = useState<string>(uuidv4())
  const t = useTranslation()
  const [chatKeyword, setChatKeyword] = useIntermediateChatKeyword()

  useEffect(() => {
    if (chatKeyword) {
      setText(chatKeyword)
    }
  }, [chatKeyword])

  const resetChat = () => {
    setMessages([])
    setText('')
    setIsLoading(false)
    setSelectedChatId(uuidv4())
    setChatKeyword('')
  }

  const handleSelectChat = async (chatId: string) => {
    try {
      setIsLoading(true)
      setSelectedChatId(chatId)

      const chatMessages = await getChatMessages(chatId)
      const uiMessages = chatMessages.messages.map((msg) => ({
        text: msg.content,
        senderType: msg.senderType,
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
