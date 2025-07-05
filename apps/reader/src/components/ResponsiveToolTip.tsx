import React from 'react'

import { cn } from '../lib/utils'

import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from './ui/tooltip'

export const ResponsiveToolTip = ({
  content,
  children,
  className,
}: React.PropsWithChildren<{
  content: string | React.ReactNode
  className?: string
}>) => {
  const [open, setOpen] = React.useState(false)

  return (
    <TooltipProvider delayDuration={0}>
      <Tooltip open={open}>
        <TooltipTrigger asChild>
          <button
            type="button"
            className={cn('cursor-pointer', className)}
            onClick={() => setOpen(!open)}
            onMouseEnter={() => setOpen(true)}
            onMouseLeave={() => setOpen(false)}
            onTouchStart={() => setOpen(!open)}
            onKeyDown={(e) => {
              e.preventDefault()
              if (e.key === 'Enter') {
                setOpen((prev) => !prev)
              }
            }}
          >
            {children}
          </button>
        </TooltipTrigger>
        <TooltipContent
          className={!content ? 'hidden' : ''}
          onMouseEnter={() => setOpen(true)}
          onMouseLeave={() => setOpen(false)}
          align="start"
        >
          <span className="inline-block">{content}</span>
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  )
}
