import { useEffect } from 'react'

export const useAutoResize = (
  text: string,
  textareaRef: {
    current: HTMLTextAreaElement | null
  },
) => {
  useEffect(() => {
    const textarea = textareaRef.current
    if (!textarea) return
    textarea.style.height = 'auto'
    textarea.style.height = `${textarea.scrollHeight}px`
  }, [text, textareaRef])
}
