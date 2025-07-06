import clsx from 'clsx'
import React, { ComponentProps, FC } from 'react'

export const Bar: FC<ComponentProps<'div'>> = ({ className, ...props }) => {
  return (
    <div
      className={clsx(
        'typescale-body-small text-outline flex h-6 items-center justify-between gap-2 px-[4vw] sm:px-2',
        className,
      )}
      {...props}
    ></div>
  )
}
