import React, { useEffect, useState } from 'react'
import { useTranslation } from '@flow/reader/hooks'
import {
  CommandDialog,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
} from '../../ui/command'
import { chatService } from '../../../services/api/chatService'
import { ChatResponse } from '../../../services/api/types'
import { TEST_USER_ID } from '../../../pages/_app'
import { Loader } from 'lucide-react'

interface ChatHistoryCommandDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  onSelectChat?: (chatId: string) => Promise<void>
}

export const ChatHistoryCommandDialog: React.FC<
  ChatHistoryCommandDialogProps
> = ({ open, onOpenChange, onSelectChat }) => {
  const t = useTranslation()
  const [chatHistory, setChatHistory] = useState<ChatResponse[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (open) {
      fetchChatHistory()
    }
  }, [open])

  const fetchChatHistory = async () => {
    setIsLoading(true)
    setError(null)
    try {
      const chats = await chatService.getUserChats(TEST_USER_ID)
      setChatHistory(chats)
    } catch (err) {
      setError(t('chat.history_fetch_error'))
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <CommandDialog open={open} onOpenChange={onOpenChange}>
      <CommandInput placeholder={t('chat.search_history')} />
      <CommandList>
        <CommandEmpty>{t('chat.no_history')}</CommandEmpty>

        <CommandGroup heading={t('chat.history')}>
          {isLoading ? (
            <CommandItem disabled>
              <Loader className="mr-2 h-4 w-4 animate-spin" />
              {t('chat.loading')}
            </CommandItem>
          ) : error ? (
            <CommandItem disabled>{error}</CommandItem>
          ) : chatHistory.length > 0 ? (
            chatHistory.map((chat) => (
              <CommandItem
                key={chat.id}
                onSelect={() => {
                  onSelectChat?.(chat.id)
                }}
              >
                <span>{chat.title || t('chat.untitled')}</span>
              </CommandItem>
            ))
          ) : (
            <CommandItem disabled>{t('chat.no_chat_history')}</CommandItem>
          )}
        </CommandGroup>
      </CommandList>
    </CommandDialog>
  )
}
