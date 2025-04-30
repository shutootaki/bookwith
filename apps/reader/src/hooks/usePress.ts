import { useState } from 'react'

import { useEventListener } from './useEventListener'

export function usePress(target: React.RefObject<HTMLElement | null> | null) {
  const [pressed, setPressed] = useState(false)
  useEventListener(target?.current, 'mousedown', () => {
    setPressed(true)
  })
  useEventListener('mouseup', () => {
    setPressed(false)
  })
  return pressed
}
