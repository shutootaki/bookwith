import { ComponentProps, forwardRef } from 'react'
import { IconType } from 'react-icons'

import { cn } from '../lib/utils'

import { Button as ShadcnButton } from './ui/button'

// shadcn-uiのButtonを再エクスポートして既存コードとの互換性を保つ
export const Button = ShadcnButton

// IconButtonをshadcn-uiのButtonを使って実装
interface IconButtonProps extends Omit<ComponentProps<typeof Button>, 'size'> {
  Icon: IconType
  size?: number
}

export const IconButton = forwardRef<HTMLButtonElement, IconButtonProps>(
  ({ className, Icon, size = 16, ...props }, ref) => {
    return (
      <Button
        variant="ghost"
        size="icon"
        className={cn('h-6 w-6', className)}
        ref={ref}
        {...props}
      >
        <Icon size={size} />
      </Button>
    )
  },
)

IconButton.displayName = 'IconButton'
