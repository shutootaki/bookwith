import { Download, Share2, Upload, Trash2, X } from 'lucide-react'
import React, { useEffect, useState } from 'react'
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
  const { startLoading, stopLoading, updateProgress, updateSubTasks } =
    useLoading({
      message: t('importing_books'),
      type: 'global',
      showProgress: true,
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
    const filesArray = Array.from(files)
    const taskId = startLoading(undefined, { filesTotal: filesArray.length })

    try {
      const result = await handleFiles(
        files,
        setLoading,
        updateProgress,
        updateSubTasks,
      )

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
        {select && (
          <div className="bg-secondary flex items-center justify-between rounded-lg p-3">
            <span className="text-secondary-foreground text-sm">
              {t('selected_books', { count: selectedBookIds.size })}
            </span>
            <Button variant="ghost" size="sm" onClick={toggleSelect}>
              <X className="h-4 w-4" />
            </Button>
          </div>
        )}
        <div>
          <TextField
            name={SOURCE}
            placeholder={t('remote_epub_placeholder')}
            type="url"
            hideLabel
            actions={[
              {
                title: t('share'),
                Icon: Share2,
                onClick(el) {
                  if (el?.reportValidity()) {
                    copy(`${window.location.origin}/?${SOURCE}=${el.value}`)
                  }
                },
              },
              {
                title: t('download'),
                Icon: Download,
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
          <div className="flex items-center gap-2">
            {books.length > 0 && (
              <Button variant="outline" size="sm" onClick={toggleSelect}>
                {t(select ? 'cancel' : 'select')}
              </Button>
            )}
            {books.length === 0 && (
              <Button
                variant="secondary"
                size="sm"
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
            {select && (
              <Button
                variant="outline"
                size="sm"
                onClick={
                  allSelected ? reset : () => books.forEach((b) => add(b.id))
                }
              >
                {t(allSelected ? 'deselect_all' : 'select_all')}
              </Button>
            )}
          </div>

          <div className="flex items-center gap-2">
            {select ? (
              <AlertDialog>
                <AlertDialogTrigger asChild>
                  <Button
                    variant="destructive"
                    size="sm"
                    disabled={selectedBookIds.size === 0}
                  >
                    <Trash2 className="h-4 w-4" />
                    {t('delete')} ({selectedBookIds.size})
                  </Button>
                </AlertDialogTrigger>
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
            ) : (
              <Button
                variant="default"
                size="sm"
                onClick={() => document.getElementById('file-import')?.click()}
              >
                <Upload className="h-4 w-4" />
                {t('import')}
              </Button>
            )}
            <input
              id="file-import"
              type="file"
              accept="application/epub+zip,application/epub,application/zip"
              className="sr-only"
              onChange={async (e) => {
                const files = e.target.files
                if (files) {
                  handleFileImport(files, setLoading)
                }
              }}
              multiple
              aria-label="import-books"
            />
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
          <p className="text-muted-foreground">{t('no_books_message')}</p>
        </div>
      )}
      <Toaster />
    </DropZone>
  )
}
