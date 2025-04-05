import { useState } from 'react'

import { useEventListener } from './useEventListener'

export function useHover(target: React.RefObject<HTMLElement | null> | null) {
  const [hovered, setHovered] = useState(false)
  useEventListener(target, 'mouseenter', () => {
    setHovered(true)
  })
  useEventListener(target, 'mouseleave', () => {
    setHovered(false)
  })
  return hovered
}
