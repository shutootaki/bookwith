import { Loader, MessageSquare } from 'lucide-react'
import React, { useEffect, useState, useCallback } from 'react'

import { useTranslation } from '@flow/reader/hooks'

import { getUserChats } from '../../lib/apiHandler/chatApiHandler'
import { components } from '../../lib/openapi-schema/schema'
import { TEST_USER_ID } from '../../pages/_app'
import {
  CommandDialog,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
} from '../ui/command'
import { DialogTitle } from '../ui/dialog'

interface ChatHistoryCommandDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  onSelectChat?: (chatId: string) => Promise<void>
}

export const ChatHistoryCommandDialog: React.FC<
  ChatHistoryCommandDialogProps
> = ({ open, onOpenChange, onSelectChat }) => {
  const t = useTranslation()
  const [chatHistory, setChatHistory] = useState<
    components['schemas']['ChatsResponse']['chats']
  >([])
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const fetchChatHistory = useCallback(async () => {
    setIsLoading(true)
    setError(null)
    try {
      const chats = await getUserChats(TEST_USER_ID)
      setChatHistory(chats.chats)
    } catch {
      setError(t('chat.history_fetch_error'))
    } finally {
      setIsLoading(false)
    }
  }, [t])

  useEffect(() => {
    if (open) {
      fetchChatHistory()
    }
  }, [open, fetchChatHistory])

  return (
    <CommandDialog open={open} onOpenChange={onOpenChange}>
      <DialogTitle className="sr-only">{t('chat.history')}</DialogTitle>
      <CommandInput placeholder={t('chat.search_history')} />
      <CommandList className="max-h-96">
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
                className="flex flex-col items-start py-3 px-2"
              >
                <div className="flex w-full items-center">
                  <MessageSquare className="text-primary/70 mr-2 h-4 w-4 flex-shrink-0" />
                  <span>{chat.title || t('chat.untitled')}</span>
                </div>
                <div className="text-muted-foreground w-full text-xs">
                  <span>
                    {t('chat.created_at')}:{' '}
                    {new Date(chat.updatedAt).toLocaleString()}
                  </span>
                </div>
              </CommandItem>
            ))
          ) : (
            <CommandItem disabled>{t('chat.no_history')}</CommandItem>
          )}
        </CommandGroup>
      </CommandList>
    </CommandDialog>
  )
}
