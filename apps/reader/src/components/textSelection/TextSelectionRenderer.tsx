import clsx from 'clsx'
import React, { useRef, useState } from 'react'
import FocusLock from 'react-focus-lock'

import { useMobile, useTypography } from '../../hooks'
import { BookTab } from '../../models'
import { scale } from '../../utils/platform'
import { layout, LayoutAnchorMode, LayoutAnchorPosition } from '../base'

import { ActionMenu } from './ActionMenu'
import { AnnotationToolbar } from './AnnotationToolbar'

const ICON_SIZE = scale(22, 28)
const ANNOTATION_SIZE = scale(28, 32)

interface TextSelectionRendererProps {
  tab: BookTab
  range: Range
  anchorRect: DOMRect
  containerRect: DOMRect
  viewRect: DOMRect
  text: string
  forward: boolean
  hide: () => void
}

export const TextSelectionRenderer: React.FC<TextSelectionRendererProps> = ({
  tab,
  range,
  anchorRect,
  containerRect,
  viewRect,
  forward,
  text,
  hide,
}) => {
  const ref = useRef<HTMLTextAreaElement>(null)
  const [width, setWidth] = useState(0)
  const [height, setHeight] = useState(0)
  const mobile = useMobile()

  const cfi = tab.rangeToCfi(range)
  const annotation = (tab.book?.annotations || []).find((a) => a.cfi === cfi)
  const [annotate, setAnnotate] = useState(!!annotation)

  const position = forward
    ? LayoutAnchorPosition.Before
    : LayoutAnchorPosition.After

  const { zoom } = useTypography(tab)
  const endContainer = forward ? range.endContainer : range.startContainer
  const _lineHeight = parseFloat(
    getComputedStyle(endContainer.parentElement!).lineHeight,
  )
  // no custom line height and the origin is keyword, e.g. 'normal'.
  const lineHeight = isNaN(_lineHeight)
    ? anchorRect.height
    : _lineHeight * (zoom ?? 1)

  return (
    <FocusLock disabled={mobile}>
      <div
        // cover `sash`
        className="fixed inset-0 z-50 bg-transparent"
        onMouseDown={hide}
      />
      <div
        ref={(el) => {
          if (!el) return
          setWidth(el.clientWidth)
          setHeight(el.clientHeight)
          if (!mobile) {
            el.focus()
          }
        }}
        className={clsx(
          'bg-card text-card-foreground absolute z-50 rounded-lg border border-gray-100 p-2 shadow-md focus:outline-none dark:border-gray-800',
        )}
        style={{
          left: layout(containerRect.width, width, {
            offset: anchorRect.left + viewRect.left - containerRect.left,
            size: anchorRect.width,
            mode: LayoutAnchorMode.ALIGN,
            position,
          }),
          top: layout(containerRect.height, height, {
            offset: anchorRect.top - (lineHeight - anchorRect.height) / 2,
            size: lineHeight,
            position,
          }),
        }}
        tabIndex={-1}
        onKeyDown={(e) => {
          e.stopPropagation()
          if (e.key === 'c' && e.ctrlKey) {
            // This will be handled by ActionMenu
          }
        }}
      >
        {annotate ? (
          <>
            <div className="mb-2">
              <textarea
                ref={ref}
                name="notes"
                defaultValue={annotation?.notes || ''}
                className="focus:border-primary focus:ring-primary h-40 w-72 rounded-lg border border-gray-200 focus:ring-1 dark:border-gray-700"
                autoFocus
              />
            </div>
            <div className="mt-2 flex">
              {annotation && (
                <button
                  className="bg-secondary text-secondary-foreground rounded-md border border-gray-200 px-3 py-1 text-sm hover:bg-gray-100 dark:border-gray-700 dark:hover:bg-gray-800"
                  onClick={() => {
                    tab.removeAnnotation(cfi)
                    hide()
                  }}
                >
                  Delete
                </button>
              )}
              <button
                className="bg-primary hover:bg-primary/90 text-primary-foreground ml-auto rounded-md px-3 py-1 text-sm shadow-sm transition-colors"
                onClick={() => {
                  tab.putAnnotation(
                    annotation?.type ?? 'highlight',
                    cfi,
                    annotation?.color ?? 'yellow',
                    text,
                    ref.current?.value,
                  )
                  hide()
                }}
              >
                {annotation ? 'Update' : 'Create'}
              </button>
            </div>
          </>
        ) : (
          <ActionMenu
            tab={tab}
            text={text}
            hide={hide}
            onAnnotate={() => setAnnotate(true)}
            iconSize={ICON_SIZE}
          />
        )}

        <AnnotationToolbar
          tab={tab}
          cfi={cfi}
          text={text}
          annotation={annotation}
          ref={ref}
          hide={hide}
          annotationSize={ANNOTATION_SIZE}
          showAnnotations={true}
        />
      </div>
    </FocusLock>
  )
}
