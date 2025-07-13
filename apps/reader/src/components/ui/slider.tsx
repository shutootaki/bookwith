import * as SliderPrimitive from '@radix-ui/react-slider'
import * as React from 'react'

import { cn } from '@flow/reader/lib/utils'

const Slider = React.forwardRef<
  React.ElementRef<typeof SliderPrimitive.Root>,
  React.ComponentPropsWithoutRef<typeof SliderPrimitive.Root>
>(({ className, ...props }, ref) => {
  // audio-progress-slider用の特別なクラス
  const isAudioProgress = className?.includes('audio-progress-slider')
  return (
    <SliderPrimitive.Root
      ref={ref}
      className={cn(
        'relative flex w-full touch-none select-none items-center',
        className,
      )}
      {...props}
    >
      <SliderPrimitive.Track
        className={cn(
          isAudioProgress
            ? 'bg-accent/30 relative h-3 w-full grow overflow-hidden rounded-full'
            : 'bg-primary/20 relative h-1.5 w-full grow overflow-hidden rounded-full',
        )}
      >
        <SliderPrimitive.Range
          className={cn(
            isAudioProgress
              ? 'bg-accent absolute h-full'
              : 'bg-primary absolute h-full',
          )}
        />
      </SliderPrimitive.Track>
      <SliderPrimitive.Thumb
        className={cn(
          isAudioProgress
            ? 'border-accent/50 bg-background focus-visible:ring-accent block h-5 w-5 rounded-full border shadow transition-colors focus-visible:outline-none focus-visible:ring-2 disabled:pointer-events-none disabled:opacity-50'
            : 'border-primary/50 bg-background focus-visible:ring-ring block h-4 w-4 rounded-full border shadow transition-colors focus-visible:outline-none focus-visible:ring-1 disabled:pointer-events-none disabled:opacity-50',
        )}
      />
    </SliderPrimitive.Root>
  )
})
Slider.displayName = SliderPrimitive.Root.displayName

export { Slider }
