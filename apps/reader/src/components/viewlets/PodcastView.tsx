import React from 'react'

import { PaneView, PaneViewProps } from '../base'
import { PodcastPane } from '../podcast'

export const PodcastView: React.FC<PaneViewProps> = (props) => {
  return (
    <PaneView {...props}>
      <PodcastPane className="p-4" />
    </PaneView>
  )
}
