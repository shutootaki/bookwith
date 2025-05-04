import clsx from 'clsx'
import { useCallback, useRef, useState } from 'react'
import FocusLock from 'react-focus-lock'
import {
  MdChat,
  MdCopyAll,
  MdOutlineAddBox,
  MdOutlineEdit,
  MdOutlineIndeterminateCheckBox,
  MdSearch,
} from 'react-icons/md'
import { useSnapshot } from 'valtio'

import {
  isForwardSelection,
  useMobile,
  useSetAction,
  useTextSelection,
  useTranslation,
  useTypography,
} from '../hooks'
import { BookTab } from '../models'
import { typeMap, colorMap } from '../utils/annotation'
import { isTouchScreen, scale } from '../utils/platform'
import { copy, keys, last } from '../utils/utils'

import { TextField } from './Form'
import { layout, LayoutAnchorMode, LayoutAnchorPosition } from './base'
import { Button } from './ui/button'

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
    <TextSelectionMenuRenderer
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

const ICON_SIZE = scale(22, 28)
const ANNOTATION_SIZE = scale(28, 32)

interface TextSelectionMenuRendererProps {
  tab: BookTab
  range: Range
  anchorRect: DOMRect
  containerRect: DOMRect
  viewRect: DOMRect
  text: string
  forward: boolean
  hide: () => void
}
const TextSelectionMenuRenderer: React.FC<TextSelectionMenuRendererProps> = ({
  tab,
  range,
  anchorRect,
  containerRect,
  viewRect,
  forward,
  text,
  hide,
}) => {
  const setAction = useSetAction()
  const ref = useRef<HTMLInputElement>(null)
  const [width, setWidth] = useState(0)
  const [height, setHeight] = useState(0)
  const mobile = useMobile()
  const t = useTranslation('menu')

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
            copy(text)
          }
        }}
      >
        {annotate ? (
          <div className="mb-2">
            <TextField
              mRef={ref}
              as="textarea"
              name="notes"
              defaultValue={annotation?.notes}
              hideLabel
              className="focus:border-primary focus:ring-primary h-40 w-72 rounded-lg border-gray-200 focus:ring-1 dark:border-gray-700"
              autoFocus
            />
          </div>
        ) : (
          <div className="text-muted-foreground mb-2 flex justify-between gap-1.5">
            <Button
              variant="ghost"
              size="icon"
              className="h-auto w-auto rounded-lg p-1.5 transition-colors hover:bg-gray-100 dark:hover:bg-gray-800"
              title={t('copy')}
              onClick={() => {
                hide()
                copy(text)
              }}
            >
              <MdCopyAll size={ICON_SIZE} />
            </Button>
            <Button
              variant="ghost"
              size="icon"
              className="h-auto w-auto rounded-lg p-1.5 transition-colors hover:bg-gray-100 dark:hover:bg-gray-800"
              title="チャットを開く"
              onClick={() => {
                hide()
                setAction('chat')
                tab.setChatKeyword(text)
              }}
            >
              <MdChat size={ICON_SIZE} />
            </Button>
            <Button
              variant="ghost"
              size="icon"
              className="h-auto w-auto rounded-lg p-1.5 transition-colors hover:bg-gray-100 dark:hover:bg-gray-800"
              title={t('search_in_book')}
              onClick={() => {
                hide()
                setAction('search')
                tab.setKeyword(text)
              }}
            >
              <MdSearch size={ICON_SIZE} />
            </Button>
            <Button
              variant="ghost"
              size="icon"
              className="h-auto w-auto rounded-lg p-1.5 transition-colors hover:bg-gray-100 dark:hover:bg-gray-800"
              title={t('annotate')}
              onClick={() => {
                setAnnotate(true)
              }}
            >
              <MdOutlineEdit size={ICON_SIZE} />
            </Button>
            {tab.isDefined(text) ? (
              <Button
                variant="ghost"
                size="icon"
                className="h-auto w-auto rounded-lg p-1.5 transition-colors hover:bg-gray-100 dark:hover:bg-gray-800"
                title={t('undefine')}
                onClick={() => {
                  hide()
                  tab.undefine(text)
                }}
              >
                <MdOutlineIndeterminateCheckBox size={ICON_SIZE} />
              </Button>
            ) : (
              <Button
                variant="ghost"
                size="icon"
                className="h-auto w-auto rounded-lg p-1.5 transition-colors hover:bg-gray-100 dark:hover:bg-gray-800"
                title={t('define')}
                onClick={() => {
                  hide()
                  tab.define([text])
                }}
              >
                <MdOutlineAddBox size={ICON_SIZE} />
              </Button>
            )}
          </div>
        )}
        <div className="space-y-2">
          {keys(typeMap).map((type) => (
            <div key={type} className="flex justify-center gap-2">
              {keys(colorMap).map((color) => (
                <div
                  key={color}
                  style={{
                    [typeMap[type].style]: colorMap[color],
                    width: ANNOTATION_SIZE,
                    height: ANNOTATION_SIZE,
                    fontSize: scale(16, 20),
                  }}
                  className={clsx(
                    'text-foreground flex cursor-pointer items-center justify-center rounded-md border border-gray-200 shadow-sm transition-transform hover:scale-105 dark:border-gray-700',
                    typeMap[type].class,
                  )}
                  onClick={() => {
                    tab.putAnnotation(
                      type,
                      cfi,
                      color,
                      text,
                      ref.current?.value,
                    )
                    hide()
                  }}
                >
                  A
                </div>
              ))}
            </div>
          ))}
        </div>
        {annotate && (
          <div className="mt-2 flex">
            {annotation && (
              <Button
                variant="secondary"
                size="sm"
                className="rounded-md border border-gray-200 hover:bg-gray-100 dark:border-gray-700 dark:hover:bg-gray-800"
                onClick={() => {
                  tab.removeAnnotation(cfi)
                  hide()
                }}
              >
                {t('delete')}
              </Button>
            )}
            <Button
              className="bg-primary hover:bg-primary/90 ml-auto rounded-md shadow-sm transition-colors"
              size="sm"
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
              {t(annotation ? 'update' : 'create')}
            </Button>
          </div>
        )}
      </div>
    </FocusLock>
  )
}
