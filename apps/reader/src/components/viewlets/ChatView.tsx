import React, { useState } from 'react'
import { History, PlusCircle } from 'lucide-react'
import { PaneViewProps, PaneView } from '../base'
import { useTranslation } from '@flow/reader/hooks'

// 分割したコンポーネントのインポート
import { ChatHistoryCommandDialog } from './chat/ChatHistoryCommandDialog'
import { ChatPane } from './chat/ChatPane'
import { Message } from './chat/types'

// メインのChatViewコンポーネント
export const ChatView: React.FC<PaneViewProps> = (props) => {
  const [messages, setMessages] = useState<Message[]>([])
  const [text, setText] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [showHistory, setShowHistory] = useState(false)
  const t = useTranslation()

  const resetChat = () => {
    setMessages([])
    setText('')
    setIsLoading(false)
  }

  const handleSelectMessage = (messageText: string) => {
    setText(messageText)
    setShowHistory(false)
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
      />

      <ChatHistoryCommandDialog
        open={showHistory}
        onOpenChange={setShowHistory}
        messages={messages}
        onSelectMessage={handleSelectMessage}
      />
    </PaneView>
  )
}
