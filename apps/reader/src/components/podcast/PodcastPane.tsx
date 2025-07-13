import React, { memo } from 'react'

import { usePodcastSelection } from '../../hooks/podcast/usePodcastSelection'
import { usePodcastsByBook } from '../../hooks/useSWR/usePodcast'
import { components } from '../../lib/openapi-schema/schema'
import { useReaderSnapshot } from '../../models'

import { LibraryPodcastView } from './LibraryPodcastView'
import { PodcastDetail } from './PodcastDetail'

export const PodcastPane: React.FC = memo(() => {
  const { focusedBookTab } = useReaderSnapshot()
  const { podcasts } = usePodcastsByBook(focusedBookTab?.book.id)
  const { selectedPodcast } = usePodcastSelection({
    podcasts,
    bookId: focusedBookTab?.book.id,
  })

  if (!focusedBookTab) {
    return <LibraryPodcastView />
  }

  return (
    <PodcastDetail
      podcast={selectedPodcast || undefined}
      book={focusedBookTab.book as components['schemas']['BookDetail']}
    />
  )
})
