import React, { useEffect, useState } from 'react'
import { MdOutlineFileDownload, MdOutlineShare } from 'react-icons/md'
import { useSet } from 'react-use'
import { toast } from 'sonner'

import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from '@flow/reader/components/ui/alert-dialog'

import { Button, TextField, DropZone } from '../components'
import { Toaster } from '../components/ui/sonner'
import { useBoolean } from '../hooks'
import { useLibrary, useBookCovers, useTranslation } from '../hooks'
import { useLoading } from '../hooks/useLoading'
import { deleteBooksFromAPI } from '../lib/apiHandler/bookApiHandler'
import { fetchBook, handleFiles } from '../lib/apiHandler/importHandlers'
import { reader, useReaderSnapshot } from '../models'
import { lock } from '../utils/styles'
import { copy } from '../utils/utils'

import { Book } from './Book'

const SOURCE = 'src'

export const Library: React.FC = () => {
  const { books, error, mutate: booksMutate } = useLibrary()
  const { covers, mutate: coversMutate, isCoverLoading } = useBookCovers()
  const t = useTranslation('home')
  const { startLoading, stopLoading, updateProgress } = useLoading({
    message: '📚 本をインポートしています...',
    type: 'global',
    showProgress: true,
    icon: '📚',
  })

  const [select, toggleSelect] = useBoolean(false)
  const [selectedBookIds, { add, has, toggle, reset }] = useSet<string>()

  const [loading, setLoading] = useState<string | undefined>()

  const { groups } = useReaderSnapshot()

  useEffect(() => {
    if (!select) reset()
  }, [reset, select])

  if (groups.length) return null
  if (!books) return null

  const allSelected = selectedBookIds.size === books.length
  if (!error) {
    booksMutate()
  }

  const handleImportOperation = async (
    operation: () => Promise<any>,
    mutate?: () => void,
    fileName?: string,
  ) => {
    const taskId = startLoading()

    try {
      // 初期進捗を設定
      if (fileName) {
        updateProgress(10, 100)
      }

      const result = await operation()

      if (result) {
        toast.success(t('import_success', { count: 1 }))
      } else {
        toast.error(t('import_failed', { count: 1 }))
      }

      if (mutate) mutate()

      return result
    } catch (error) {
      console.error(t('import_error_log'), error)
      toast.error(t('import_error'))
      return null
    } finally {
      stopLoading(taskId)
    }
  }

  const handleFileImport = async (
    files: FileList | File[],
    setLoading: React.Dispatch<React.SetStateAction<string | undefined>>,
  ) => {
    const taskId = startLoading()
    try {
      const result = await handleFiles(files, setLoading, updateProgress)

      if (result) {
        const { success, failed } = result
        if (success > 0 || failed > 0) {
          let message = ''
          if (success > 0 && failed === 0) {
            message = t('import_success', { count: success })
          } else if (success === 0 && failed > 0) {
            message = t('import_failed', { count: failed })
          } else {
            message = t('import_partial_success', {
              success: success,
              failed: failed,
            })
          }

          if (success > 0) {
            toast.success(message)
            booksMutate()
            coversMutate()
          } else {
            toast.error(message)
          }
        }
      }
    } catch (error) {
      console.error(t('file_import_error_log'), error)
      toast.error(t('import_error'))
    } finally {
      stopLoading(taskId)
    }
  }

  console.log({ 'loading-now': loading })
  console.log({ books })

  return (
    <DropZone
      className="scroll-parent h-full p-4"
      onDrop={(e) => {
        const bookId = e.dataTransfer.getData('text/plain')
        const book = books.find((b) => b.id === bookId)
        if (book) reader.addTab(book as any)

        handleFileImport(e.dataTransfer.files, setLoading)
      }}
    >
      <div className="mb-4 space-y-2.5">
        <div>
          <TextField
            name={SOURCE}
            placeholder="https://link.to/remote.epub"
            type="url"
            hideLabel
            actions={[
              {
                title: t('share'),
                Icon: MdOutlineShare,
                onClick(el) {
                  if (el?.reportValidity()) {
                    copy(`${window.location.origin}/?${SOURCE}=${el.value}`)
                  }
                },
              },
              {
                title: t('download'),
                Icon: MdOutlineFileDownload,
                onClick: async (el) => {
                  if (el?.reportValidity()) {
                    await handleImportOperation(
                      async () => await fetchBook(el.value, setLoading),
                      coversMutate,
                    )
                  }
                },
              },
            ]}
          />
        </div>
        <div className="flex items-center justify-between gap-4">
          <div className="space-x-2">
            {books.length ? (
              <Button variant="secondary" onClick={toggleSelect}>
                {t(select ? 'cancel' : 'select')}
              </Button>
            ) : (
              <Button
                variant="secondary"
                disabled={!books}
                onClick={async () => {
                  const fileName =
                    'Fundamental-Accessibility-Tests-Basic-Functionality-v1.0.0.epub'
                  await handleImportOperation(
                    async () => {
                      return await fetchBook(
                        'https://epubtest.org/books/Fundamental-Accessibility-Tests-Basic-Functionality-v1.0.0.epub',
                        (id) => {
                          setLoading(id)
                          if (id) {
                            updateProgress(60, 100)
                          } else {
                            updateProgress(90, 100)
                          }
                        },
                      )
                    },
                    booksMutate,
                    fileName,
                  )
                }}
              >
                {t('download_sample_book')}
              </Button>
            )}
            {select &&
              (allSelected ? (
                <Button variant="secondary" onClick={reset}>
                  {t('deselect_all')}
                </Button>
              ) : (
                <Button
                  variant="secondary"
                  onClick={() => books.forEach((b) => add(b.id))}
                >
                  {t('select_all')}
                </Button>
              ))}
          </div>

          <div className="space-x-2">
            {select ? (
              <>
                <AlertDialog>
                  <Button asChild>
                    <AlertDialogTrigger>{t('delete')}</AlertDialogTrigger>
                  </Button>
                  <AlertDialogContent>
                    <AlertDialogHeader>
                      <AlertDialogTitle>
                        {t('delete_confirmation')}
                      </AlertDialogTitle>
                      <AlertDialogDescription>
                        {t('delete_confirmation_message')}
                      </AlertDialogDescription>
                    </AlertDialogHeader>
                    <AlertDialogFooter>
                      <AlertDialogCancel>{t('cancel')}</AlertDialogCancel>
                      <AlertDialogAction
                        onClick={async () => {
                          toggleSelect()
                          await deleteBooksFromAPI([...selectedBookIds])
                          booksMutate()
                          toast.success(t('delete_success'))
                        }}
                      >
                        {t('delete')}
                      </AlertDialogAction>
                    </AlertDialogFooter>
                  </AlertDialogContent>
                </AlertDialog>
              </>
            ) : (
              <>
                <Button className="relative">
                  <input
                    type="file"
                    accept="application/epub+zip,application/epub,application/zip"
                    className="absolute inset-0 cursor-pointer opacity-0"
                    onChange={async (e) => {
                      const files = e.target.files
                      if (files) {
                        handleFileImport(files, setLoading)
                      }
                    }}
                    multiple
                    aria-label="import-books"
                  />
                  {t('import')}
                </Button>
              </>
            )}
          </div>
        </div>
      </div>
      {books.length > 0 ? (
        <div className="scroll h-full">
          <ul
            className="grid"
            style={{
              gridTemplateColumns: `repeat(auto-fill, minmax(calc(80px + 3vw), 1fr))`,
              columnGap: lock(16, 32),
              rowGap: lock(24, 40),
            }}
          >
            {books.map((book) => (
              <Book
                key={book.id}
                book={book as any}
                covers={covers}
                select={select}
                selected={has(book.id)}
                loading={loading === book.id}
                toggle={toggle}
                isLoading={isCoverLoading}
              />
            ))}
          </ul>
        </div>
      ) : (
        <div className="flex h-full items-center justify-center">
          <p className="text-on-surface-variant">{t('no_books_message')}</p>
        </div>
      )}
      <Toaster />
    </DropZone>
  )
}
