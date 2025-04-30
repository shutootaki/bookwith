import { useEffect } from 'react'

import { TextAreaRefType } from './types'

export const useAutoResize = (text: string, textareaRef: TextAreaRefType) => {
  useEffect(() => {
    const textarea = textareaRef.current
    if (!textarea) return
    textarea.style.height = 'auto'
    textarea.style.height = `${textarea.scrollHeight}px`
  }, [text, textareaRef])
}
