import React from 'react'
import { MdChat, MdCopyAll, MdOutlineEdit, MdSearch } from 'react-icons/md'

import { useSetAction, useTranslation } from '../../hooks'
import { BookTab } from '../../models'
import { copy } from '../../utils/utils'
import { Button } from '../ui/button'

interface ActionMenuProps {
  tab: BookTab
  text: string
  hide: () => void
  onAnnotate: () => void
  iconSize: number
}

export const ActionMenu: React.FC<ActionMenuProps> = ({
  tab,
  text,
  hide,
  onAnnotate,
  iconSize,
}) => {
  const setAction = useSetAction()
  const t = useTranslation('menu')

  return (
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
        <MdCopyAll size={iconSize} />
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
        <MdChat size={iconSize} />
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
        <MdSearch size={iconSize} />
      </Button>
      <Button
        variant="ghost"
        size="icon"
        className="h-auto w-auto rounded-lg p-1.5 transition-colors hover:bg-gray-100 dark:hover:bg-gray-800"
        title={t('annotate')}
        onClick={onAnnotate}
      >
        <MdOutlineEdit size={iconSize} />
      </Button>
      {/* NOTE: Annotationとの使い分けが曖昧なので、一旦コメントアウト */}
      {/* {tab.isDefined(text) ? (
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
          <MdOutlineIndeterminateCheckBox size={iconSize} />
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
          <MdOutlineAddBox size={iconSize} />
        </Button>
      )} */}
    </div>
  )
}
