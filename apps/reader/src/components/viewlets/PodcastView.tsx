import React from 'react'

import { PaneViewProps } from '../base'
import { PodcastPane } from '../podcast'

export const PodcastView: React.FC<PaneViewProps> = () => {
  return (
    <div className="flex h-full flex-col">
      <PodcastPane />
    </div>
  )
}
