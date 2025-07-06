import clsx from 'clsx'
import React, { FC } from 'react'
import { useSnapshot } from 'valtio'

import { BookTab } from '../../models'

import { Bar } from './Bar'

interface ReaderPaneFooterProps {
  tab: BookTab
}

export const ReaderPaneFooter: FC<ReaderPaneFooterProps> = ({ tab }) => {
  const { locationToReturn, location, book } = useSnapshot(tab)

  return (
    <Bar>
      {locationToReturn ? (
        <>
          <button
            className={clsx(locationToReturn || 'invisible')}
            onClick={() => {
              tab.hidePrevLocation()
              tab.display(locationToReturn.end.cfi, false)
            }}
          >
            Return to {locationToReturn.end.cfi}
          </button>
          <button
            onClick={() => {
              tab.hidePrevLocation()
            }}
          >
            Stay
          </button>
        </>
      ) : (
        <>
          <div>{location?.start.href}</div>
          <div>{((book?.percentage ?? 0) * 100).toFixed()}%</div>
        </>
      )}
    </Bar>
  )
}
