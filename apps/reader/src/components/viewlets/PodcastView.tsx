import React from 'react'

import { PaneView, PaneViewProps } from '../base'
import { PodcastPane } from '../podcast'

export const PodcastView: React.FC<PaneViewProps> = (props) => {
  return (
    <PaneView {...props}>
      <div className="scroll">
        <PodcastPane className="p-4" />
      </div>
    </PaneView>
  )
}
