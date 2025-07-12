import clsx from 'clsx'
import { motion } from 'framer-motion'
import { useRouter } from 'next/router'
import React from 'react'
import { MdCheckBox, MdCheckBoxOutlineBlank } from 'react-icons/md'

import { useMobile } from '../hooks'
import { components } from '../lib/openapi-schema/schema'
import { reader } from '../models'

const placeholder = `data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1 1"><rect fill="gray" fill-opacity="0" width="1" height="1"/></svg>`

export const BookSkeleton: React.FC = () => {
  return (
    <motion.li
      className="relative flex flex-col"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.3 }}
    >
      <div className="relative overflow-hidden rounded-sm shadow-sm">
        <div className="relative aspect-[9/12] animate-pulse bg-gray-200 dark:bg-gray-800">
          <div className="absolute inset-0 -translate-x-full animate-[shimmer_2s_infinite] bg-gradient-to-r from-transparent via-gray-300/50 to-transparent dark:via-gray-700/50" />
        </div>
      </div>

      <div className="mt-3 space-y-2">
        <div className="h-4 w-3/4 animate-pulse rounded bg-gray-200 dark:bg-gray-800" />
        <div className="h-3 w-1/2 animate-pulse rounded bg-gray-200 dark:bg-gray-800" />
      </div>
    </motion.li>
  )
}

export const Book: React.FC<{
  book?: components['schemas']['BookDetail']
  covers?: components['schemas']['CoversResponse']['covers']
  select?: boolean
  selected?: boolean
  loading?: boolean
  toggle?: (id: string) => void
  isLoading?: boolean
}> = ({ book, covers, select, selected, loading, toggle, isLoading }) => {
  const router = useRouter()
  const mobile = useMobile()

  if (isLoading || !book || !covers) {
    return <BookSkeleton />
  }

  const coverData = covers.find((c) => c.bookId === book.id)
  const cover = coverData?.coverUrl
  const displayTitle = book.metadataTitle ?? book.name
  console.log('cover', cover)

  const altText = cover
    ? `Cover of ${displayTitle}`
    : `Loading cover for ${displayTitle}`

  const Icon = selected ? MdCheckBox : MdCheckBoxOutlineBlank

  return (
    <div
      className={clsx(
        'relative flex flex-col transition-all duration-200',
        select && 'hover:scale-105',
      )}
    >
      <div
        role="button"
        className={clsx(
          'border-inverse-on-surface relative overflow-hidden border',
          loading && 'cursor-progress',
          select && 'cursor-pointer hover:border-blue-500',
          select && selected && 'border-blue-500 ring-2 ring-blue-500',
        )}
        onClick={async () => {
          if (loading) return
          if (select && toggle) {
            toggle(book.id)
          } else {
            if (mobile) await router.push('/_')
            reader.addTab(book)
          }
        }}
      >
        <div
          className={clsx(
            'absolute bottom-0 h-1 bg-blue-500',
            loading && 'progress-bit w-[5%]',
          )}
        />
        {book?.percentage !== undefined && (
          <div className="typescale-body-large absolute right-0 bg-gray-500/60 px-2 text-gray-100">
            {(book?.percentage * 100).toFixed()}%
          </div>
        )}
        <motion.img
          src={cover ?? placeholder}
          alt={altText}
          role="img"
          aria-label={cover ? 'book-cover' : 'loading-book-cover'}
          className="mx-auto aspect-[9/12] object-cover"
          draggable={false}
          initial={{ opacity: 0.3 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.3 }}
        />
        {select && (
          <div className="absolute bottom-2 right-2 rounded-full bg-white p-1 shadow-lg dark:bg-gray-900">
            <Icon
              size={20}
              className={clsx(
                selected ? 'text-blue-500' : 'text-gray-400',
                'transition-colors duration-200',
              )}
            />
          </div>
        )}
      </div>

      <div
        className="line-clamp-2 text-on-surface-variant typescale-body-small lg:typescale-body-medium mt-2 w-full"
        title={book.name}
      >
        {displayTitle}
      </div>
    </div>
  )
}
