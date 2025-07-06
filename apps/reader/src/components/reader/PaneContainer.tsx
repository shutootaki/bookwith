import clsx from 'clsx'
import React, { FC, PropsWithChildren } from 'react'

interface PaneContainerProps {
  active: boolean
}

export const PaneContainer: FC<PropsWithChildren<PaneContainerProps>> = ({
  active,
  children,
}) => {
  return <div className={clsx('h-full', active || 'hidden')}>{children}</div>
}
