import { ArrowUpIcon } from 'lucide-react'
import React, { useRef, useEffect, useState } from 'react'

import { useAction, useTranslation } from '@flow/reader/hooks'

import { useAutoResize } from '../../hooks/useAutoResize'
import { Button } from '../ui/button'
import { Textarea } from '../ui/textarea'
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '../ui/tooltip'

interface ChatInputFormProps {
  text: string
  setText: React.Dispatch<React.SetStateAction<string>>
  onSend: (e: React.FormEvent | React.KeyboardEvent) => void
  isLoading: boolean
}

export const ChatInputForm: React.FC<ChatInputFormProps> = ({
  text,
  setText,
  onSend,
  isLoading,
}) => {
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const isEmpty = !text.trim()
  const t = useTranslation()
  const [action] = useAction()
  const [shouldFocusInput, setShouldFocusInput] = useState(false)
  const actualRef = textareaRef
  useAutoResize(text, actualRef)

  useEffect(() => {
    setShouldFocusInput(action === 'chat')
  }, [action])

  // useEffect(() => {
  //   if (textareaRef.current) {
  //     textareaRef.current = textareaRef.current
  //   }
  // }, [textareaRef])

  useEffect(() => {
    if (shouldFocusInput && textareaRef.current) {
      textareaRef.current.focus()
    }
  }, [shouldFocusInput])

  return (
    <div className="sticky bottom-0 border-t p-3">
      <form onSubmit={onSend} className="flex w-full gap-1">
        <div className="bg-background w-full rounded-lg border p-2">
          <Textarea
            ref={textareaRef}
            value={text}
            onChange={(e) => {
              setText(e.target.value)
            }}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) {
                e.preventDefault()
                onSend(e)
              }
            }}
            placeholder={t('chat.placeholder')}
            className="max-h-[300px] min-h-[30px] resize-none overflow-y-auto border-0 shadow-none focus-visible:ring-0"
            style={{ overflow: text ? 'auto' : 'hidden' }}
            disabled={isLoading}
          />

          <div className="mt-2 flex items-center justify-end">
            <TooltipProvider delayDuration={200}>
              <Tooltip>
                <TooltipTrigger asChild>
                  <Button
                    size="icon"
                    disabled={isEmpty || isLoading}
                    className="h-6 w-6 rounded-full"
                    type="submit"
                    aria-label={t('chat.send')}
                  >
                    <ArrowUpIcon className="h-4 w-4" />
                  </Button>
                </TooltipTrigger>
                <TooltipContent>{t('chat.keyboard_shortcut')}</TooltipContent>
              </Tooltip>
            </TooltipProvider>
          </div>
        </div>
      </form>
    </div>
  )
}
