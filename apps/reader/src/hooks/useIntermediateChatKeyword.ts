import { useState, useEffect } from 'react'

import { useReaderSnapshot, reader } from '../models'

// When inputting with IME and storing state in `valtio`,
// unexpected rendering with `e.target.value === ''` occurs,
// which leads to `<input>` and IME flash to empty,
// while this will not happen when using `React.useState`,

// so we should create an intermediate `chatKeyword` state to fix this.
export function useIntermediateChatKeyword() {
  const [chatKeyword, setChatKeyword] = useState('')
  const { focusedBookTab } = useReaderSnapshot()

  useEffect(() => {
    setChatKeyword(focusedBookTab?.chatKeyword ?? '')
  }, [focusedBookTab?.chatKeyword])

  useEffect(() => {
    reader.focusedBookTab?.setChatKeyword(chatKeyword)
  }, [chatKeyword])

  return [chatKeyword, setChatKeyword] as const
}
