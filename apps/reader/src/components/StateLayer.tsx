import clsx from 'clsx'
import React, { useContext, useRef, useEffect } from 'react'

import { usePress, useEventListener, useHover } from '../hooks'

interface ContextType {
  ripple?: boolean
}

const Context = React.createContext<ContextType>({})

export const StateLayer = () => {
  const ref = useRef<HTMLDivElement>(null)
  const parent = useRef<HTMLElement | null>(null)

  useEffect(() => {
    if (ref.current) {
      parent.current = ref.current.parentElement as HTMLElement
    }
  }, [])

  const { ripple: enabled = false } = useContext(Context)
  const hovered = useHover(parent)
  const pressed = usePress(parent)

  // イベントリスナーの設定を修正
  useEventListener(
    () => parent.current,
    'mousedown',
    (e: MouseEvent) => {
      if (!enabled) return
      e.stopPropagation()

      if (!ref.current) return
      const parentElement = ref.current.parentElement
      if (!parentElement) return

      const ripple = document.createElement('span')
      const diameter = Math.max(
        parentElement.clientWidth,
        parentElement.clientHeight,
      )
      const radius = diameter / 2
      const { left, top } = parentElement.getBoundingClientRect()

      ripple.style.width = ripple.style.height = `${diameter}px`
      ripple.style.left = `${e.clientX - left - radius}px`
      ripple.style.top = `${e.clientY - top - radius}px`
      ripple.classList.add('ripple')

      ripple.addEventListener('animationend', () => {
        ripple.remove()
      })

      ref.current.appendChild(ripple)
    },
  )

  return (
    <div
      className="pointer-events-none absolute inset-0 overflow-hidden"
      style={{ borderRadius: 'inherit' }}
      ref={ref}
    >
      <div
        className={clsx(
          'absolute inset-0',
          'bg-current opacity-0',
          hovered && 'opacity-hover',
          pressed && 'opacity-pressed',
        )}
      />
    </div>
  )
}
