import * as React from 'react'
import { cn } from '@flow/reader/lib/utils'

interface CircularProgressProps extends React.HTMLAttributes<HTMLDivElement> {
  size?: 'sm' | 'md' | 'lg'
  thickness?: 'thin' | 'normal' | 'thick'
}

const CircularProgress = React.forwardRef<
  HTMLDivElement,
  CircularProgressProps
>(({ className, size = 'md', thickness = 'normal', ...props }, ref) => {
  const sizeClasses = {
    sm: 'h-4 w-4',
    md: 'h-8 w-8',
    lg: 'h-12 w-12',
  }

  const thicknessClasses = {
    thin: 'border-2',
    normal: 'border-[3px]',
    thick: 'border-4',
  }

  return (
    <div
      className={cn(
        'animate-spin rounded-full border-solid border-t-transparent',
        sizeClasses[size],
        thicknessClasses[thickness],
        className,
      )}
      ref={ref}
      {...props}
    />
  )
})

CircularProgress.displayName = 'CircularProgress'

export { CircularProgress }
