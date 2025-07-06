import React, { useCallback } from 'react'
import { useSnapshot } from 'valtio'

import { isForwardSelection, useTextSelection } from '../../hooks'
import { BookTab } from '../../models'
import { isTouchScreen } from '../../utils/platform'
import { last } from '../../utils/utils'

import { TextSelectionRenderer } from './TextSelectionRenderer'

interface TextSelectionMenuProps {
  tab: BookTab
}

export const TextSelectionMenu: React.FC<TextSelectionMenuProps> = ({
  tab,
}) => {
  const { rendition, annotationRange } = useSnapshot(tab)

  // `manager` is not reactive, so we need to use getter
  const view = useCallback(() => {
    return rendition?.manager?.views._views[0]
  }, [rendition])

  const win = view()?.window
  const [selection, setSelection] = useTextSelection(win)

  const el = view()?.element as HTMLElement
  if (!el) return null

  // it is possible that both `selection` and `tab.annotationRange`
  // are set when select end within an annotation
  const range = selection?.getRangeAt(0) ?? annotationRange
  if (!range) return null

  // prefer to display above the selection to avoid text selection helpers
  // https://stackoverflow.com/questions/68081757/hide-the-two-text-selection-helpers-in-mobile-browsers
  const forward = isTouchScreen
    ? false
    : selection
    ? isForwardSelection(selection)
    : true

  const rects = [...range.getClientRects()].filter((r) => Math.round(r.width))
  const anchorRect = rects && (forward ? last(rects) : rects[0])
  if (!anchorRect) return null

  const contents = range.cloneContents()
  const text = contents.textContent?.trim()
  if (!text) return null

  return (
    // to reset inner state
    <TextSelectionRenderer
      tab={tab}
      range={range as Range}
      anchorRect={anchorRect}
      containerRect={el.parentElement!.getBoundingClientRect()}
      viewRect={el.getBoundingClientRect()}
      text={text}
      forward={forward}
      hide={() => {
        if (selection) {
          selection.removeAllRanges()
          setSelection(undefined)
        }
        /**
         * {@link range}
         */
        if (tab.annotationRange) {
          tab.annotationRange = undefined
        }
      }}
    />
  )
}
