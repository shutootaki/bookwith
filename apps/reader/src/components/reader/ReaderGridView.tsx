import clsx from 'clsx'
import React from 'react'

import { useEventListener } from '../../hooks'
import { reader, useReaderSnapshot } from '../../models'
import { SplitView } from '../base/SplitView'

import { ReaderGroup } from './ReaderGroup'
import { handleKeyDown } from './eventHandlers'

export function ReaderGridView() {
  const { groups } = useReaderSnapshot()

  useEventListener('keydown', handleKeyDown(reader.focusedBookTab))

  if (!groups.length) return null
  return (
    <SplitView className={clsx('ReaderGridView')}>
      {/* @ts-ignore */}
      {groups.map((group, i) => (
        <ReaderGroup key={group.id.toString()} index={i} />
      ))}
    </SplitView>
  )
}
