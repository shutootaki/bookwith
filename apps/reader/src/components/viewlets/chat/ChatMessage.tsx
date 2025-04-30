import { Check, Copy } from 'lucide-react'
import React, { useState } from 'react'

import { FormattedText } from '../../FormattedText'
import { Button } from '../../ui/button'

import { Message } from './types'

interface ChatMessageProps {
  message: Message
}

export const ChatMessage: React.FC<ChatMessageProps> = ({ message }) => {
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

  return message.senderType === 'user' ? (
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
        {message.text && (
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
        )}
      </div>
    </div>
  )
}
