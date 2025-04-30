import { useState, RefObject } from 'react'

import { useEventListener } from './useEventListener'

export function useHover(target: RefObject<HTMLElement | null> | null) {
  const [hovered, setHovered] = useState(false)
  useEventListener(target?.current, 'mouseenter', () => {
    setHovered(true)
  })
  useEventListener(target?.current, 'mouseleave', () => {
    setHovered(false)
  })
  return hovered
}
