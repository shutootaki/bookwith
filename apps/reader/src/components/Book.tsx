import clsx from 'clsx'
import { motion } from 'framer-motion'
import { useRouter } from 'next/router'
import React from 'react'
import { useEffect, useState } from 'react'
import { MdCheckBox, MdCheckBoxOutlineBlank } from 'react-icons/md'

import { useMobile } from '../hooks'
import { components } from '../lib/openapi-schema/schema'
import { reader } from '../models'

const placeholder = `data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1 1"><rect fill="gray" fill-opacity="0" width="1" height="1"/></svg>`

export const LoadingBookPlaceholder: React.FC<{
  identifier: string
  progress: number
}> = ({ identifier, progress }) => {
  // State for shimmer animation
  const [shimmerPosition, setShimmerPosition] = useState(-100)

  // Control shimmer animation
  useEffect(() => {
    const interval = setInterval(() => {
      setShimmerPosition((prev) => (prev > 100 ? -100 : prev + 1))
    }, 20)
    return () => clearInterval(interval)
  }, [])

  return (
    <motion.li
      key={identifier}
      className="relative flex flex-col"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.6, ease: 'easeOut' }}
    >
      {/* Book cover container */}
      <div className="relative overflow-hidden rounded-sm border border-gray-100 shadow-sm dark:border-gray-800">
        {/* Minimalist book cover */}
        <div className="relative aspect-[9/12] bg-gray-50 dark:bg-gray-900">
          {/* Subtle left edge/spine */}
          <div className="absolute left-0 top-0 h-full w-[3px] bg-gray-200 dark:bg-gray-800"></div>

          {/* Minimal content placeholders */}
          <div className="absolute top-[30%] left-1/2 h-[1px] w-2/3 -translate-x-1/2 transform bg-gray-200 dark:bg-gray-700"></div>
          <div className="absolute top-[30%] left-1/2 mt-4 h-[1px] w-1/2 -translate-x-1/2 transform bg-gray-200 dark:bg-gray-700"></div>
          <div className="absolute top-[30%] left-1/2 mt-8 h-[1px] w-1/3 -translate-x-1/2 transform bg-gray-200 dark:bg-gray-700"></div>

          {/* Elegant shimmer effect */}
          <div
            className="absolute inset-0 bg-gradient-to-r from-transparent via-white to-transparent opacity-10 dark:via-gray-800"
            style={{
              transform: `translateX(${shimmerPosition}%)`,
              transition: 'transform 0.1s linear',
            }}
          ></div>
        </div>

        {/* Refined progress indicator */}
        <motion.div
          className="absolute bottom-0 left-0 h-[2px] bg-gray-400 dark:bg-gray-500"
          style={{ width: `${progress}%` }}
          initial={{ width: 0 }}
          animate={{ width: `${progress}%` }}
          transition={{ duration: 0.5, ease: 'easeInOut' }}
        />
      </div>

      {/* Refined book title */}
      <div className="mt-3 space-y-2">
        <div className="h-4 w-3/4 rounded-sm bg-gray-100 dark:bg-gray-800"></div>
        <div className="h-4 w-1/2 rounded-sm bg-gray-100 dark:bg-gray-800"></div>

        {/* Subtle loading text */}
        <motion.div
          className="mt-1 text-xs font-light tracking-wide text-gray-400 opacity-80 dark:text-gray-500"
          initial={{ opacity: 0 }}
          animate={{ opacity: 0.8 }}
          transition={{ duration: 0.6, delay: 0.2 }}
        >
          {progress < 100 ? `Loading ${identifier}` : identifier}
        </motion.div>
      </div>
    </motion.li>
  )
}

export const Book: React.FC<{
  book: components['schemas']['BookDetail']
  covers: components['schemas']['CoversResponse']['covers']
  select?: boolean
  selected?: boolean
  loading?: boolean
  toggle: (id: string) => void
}> = ({ book, covers, select, selected, loading, toggle }) => {
  const router = useRouter()
  const mobile = useMobile()

  const coverData = covers.find((c) => c.bookId === book.id)
  const cover = coverData?.coverUrl

  const Icon = selected ? MdCheckBox : MdCheckBoxOutlineBlank

  return (
    <div className="relative flex flex-col">
      <div
        role="button"
        className={clsx(
          'border-inverse-on-surface relative border',
          loading && 'cursor-progress',
        )}
        onClick={async () => {
          if (loading) return
          if (select) {
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
        <img
          src={cover ?? placeholder}
          alt="Cover"
          className="mx-auto aspect-[9/12] object-cover"
          draggable={false}
        />
        {select && (
          <div className="absolute bottom-1 right-1">
            <Icon
              size={24}
              className={clsx(
                '-m-1',
                selected ? 'text-tertiary' : 'text-outline',
              )}
            />
          </div>
        )}
      </div>

      <div
        className="line-clamp-2 text-on-surface-variant typescale-body-small lg:typescale-body-medium mt-2 w-full"
        title={book.name}
      >
        {typeof book.bookMetadata?.title === 'string' && book.bookMetadata.title
          ? book.bookMetadata.title
          : book.name}
      </div>
    </div>
  )
}
