import React from 'react'
import { useTranslation } from '@flow/reader/hooks'
import {
  CommandDialog,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
} from '../../ui/command'
import { Message } from './types'

interface ChatHistoryCommandDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  messages: Message[]
  onSelectMessage: (text: string) => void
}

export const ChatHistoryCommandDialog: React.FC<
  ChatHistoryCommandDialogProps
> = ({ open, onOpenChange, messages, onSelectMessage }) => {
  const t = useTranslation()

  return (
    <CommandDialog open={open} onOpenChange={onOpenChange}>
      <CommandInput placeholder={t('chat.search_history')} />
      <CommandList>
        <CommandEmpty>{t('chat.no_history')}</CommandEmpty>
        <CommandGroup heading={t('chat.history')}>
          {messages.length > 0 ? (
            messages
              .filter((msg) => msg.sender_type === 'user')
              .map((msg, index) => (
                <CommandItem
                  key={index}
                  onSelect={() => onSelectMessage(msg.text)}
                >
                  <span>
                    {msg.text.length > 50
                      ? `${msg.text.slice(0, 50)}...`
                      : msg.text}
                  </span>
                </CommandItem>
              ))
          ) : (
            <CommandItem>{t('chat.no_history')}</CommandItem>
          )}
        </CommandGroup>
      </CommandList>
    </CommandDialog>
  )
}
