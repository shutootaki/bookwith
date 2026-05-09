import clsx from 'clsx'
import React, { useCallback } from 'react'
import { MdWebAsset } from 'react-icons/md'
import { RiBookLine } from 'react-icons/ri'
import { useSnapshot } from 'valtio'

import { useTranslation } from '../../hooks'
import { apiClient } from '../../lib/apiHandler/apiClient'
import { handleFiles } from '../../lib/apiHandler/importHandlers'
import { BookTab, reader, useReaderSnapshot } from '../../models'
import { isTouchScreen } from '../../utils/platform'
import { Tab } from '../Tab'
import { DropZone } from '../base'
import { useSplitViewItem } from '../base/SplitView'
import * as pages from '../pages'

import { BookPane } from './BookPane'
import { PaneContainer } from './PaneContainer'

// F-1: ドラッグ&ドロップで `text/plain` 由来の id をパス引数として API に渡す前に
// UUID 形式を強制する。`../admin/users` などのパス変造を阻止する。
const UUID_RE =
  /^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$/

interface ReaderGroupProps {
  index: number
}

export function ReaderGroup({ index }: ReaderGroupProps) {
  const group = reader.groups[index]
  if (!group) return null

  const { focusedIndex } = useReaderSnapshot()
  const { tabs, selectedIndex } = useSnapshot(group as any)
  const t = useTranslation()

  const { size } = useSplitViewItem(`ReaderGroup.${index}`, {
    // to disable sash resize
    visible: false,
  })

  const handleMouseDown = useCallback(() => {
    reader.selectGroup(index)
  }, [index])

  return (
    <div
      className="ReaderGroup flex flex-1 flex-col overflow-hidden focus:outline-none"
      onMouseDown={handleMouseDown}
      style={{ width: size }}
    >
      <Tab.List
        className="hidden sm:flex"
        onDelete={() => reader.removeGroup(index)}
      >
        {tabs.map((tab: any, i: number) => {
          const selected = i === selectedIndex
          const focused = index === focusedIndex && selected
          return (
            <Tab
              key={tab.id}
              selected={selected}
              focused={focused}
              onClick={() => group.selectTab(i)}
              onDelete={() => reader.removeTab(i, index)}
              Icon={tab instanceof BookTab ? RiBookLine : MdWebAsset}
              draggable
              onDragStart={(e) => {
                e.dataTransfer.setData('text/plain', `${index},${i}`)
              }}
            >
              {tab.isBook ? tab.title : t(`${tab.title}.title`)}
            </Tab>
          )
        })}
      </Tab.List>

      <DropZone
        className={clsx('flex-1', isTouchScreen || 'h-0')}
        split
        onDrop={async (e, position) => {
          // read `e.dataTransfer` first to avoid get empty value after `await`
          const files = e.dataTransfer.files
          let tabs = []

          if (files.length) {
            const result = await handleFiles(files)
            if (result.newBooks) {
              tabs = result.newBooks
            }
          } else {
            const text = e.dataTransfer.getData('text/plain')
            const fromTab = text.includes(',')

            if (fromTab) {
              const indexes = text.split(',')
              const groupIdx = Number(indexes[0])

              if (index === groupIdx) {
                if (group.tabs.length === 1) return
                if (position === 'universe') return
              }

              const tabIdx = Number(indexes[1])
              const tab = reader.removeTab(tabIdx, groupIdx)
              if (tab) tabs.push(tab)
            } else {
              const id = text
              const matchedPage = Object.values(pages).find(
                (p) => p.displayName === id,
              )
              if (matchedPage) {
                tabs.push(matchedPage)
              } else if (UUID_RE.test(id)) {
                const tabParam = await apiClient<any>(`/books/${id}`).catch(
                  () => undefined,
                )
                if (tabParam) tabs.push(tabParam)
              }
            }
          }

          if (tabs.length) {
            switch (position) {
              case 'left':
                reader.addGroup(tabs, index)
                break
              case 'right':
                reader.addGroup(tabs, index + 1)
                break
              default:
                tabs.forEach((t) => reader.addTab(t, index))
            }
          }
        }}
      >
        {group.tabs.map((tab: any, i: number) => (
          <PaneContainer active={i === selectedIndex} key={tab.id}>
            {tab instanceof BookTab ? (
              <BookPane tab={tab} onMouseDown={handleMouseDown} />
            ) : (
              <tab.Component />
            )}
          </PaneContainer>
        ))}
      </DropZone>
    </div>
  )
}
