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
import ImportProgress, {
  ImportProgressState,
} from '../components/ImportProgress'
import { Toaster } from '../components/ui/sonner'
import { useBoolean } from '../hooks'
import { useLibrary, useBookCovers, useTranslation } from '../hooks'
import { deleteBooksFromAPI } from '../lib/apiHandler/bookApiHandler'
import { fetchBook, handleFiles } from '../lib/apiHandler/importHandlers'
import { reader, useReaderSnapshot } from '../models'
import { lock } from '../utils/styles'
import { copy } from '../utils/utils'

import { LoadingBookPlaceholder } from './Book'
import { Book } from './Book'

const SOURCE = 'src'

export const Library: React.FC = () => {
  const { books, error, mutate: booksMutate } = useLibrary()
  const { covers, mutate: coversMutate, isCoverLoading } = useBookCovers()
  const t = useTranslation('home')

  const [select, toggleSelect] = useBoolean(false)
  const [selectedBookIds, { add, has, toggle, reset }] = useSet<string>()

  const [loading, setLoading] = useState<string | undefined>()
  const [importProgress, setImportProgress] = useState<ImportProgressState>({
    total: 0,
    completed: 0,
    importing: false,
  })

  const { groups } = useReaderSnapshot()

  useEffect(() => {
    if (!select) reset()
  }, [reset, select])

  useEffect(() => {
    if (
      importProgress.success !== undefined &&
      importProgress.failed !== undefined &&
      !importProgress.importing &&
      importProgress.total > 0
    ) {
      const successCount = importProgress.success
      const failedCount = importProgress.failed

      if (successCount > 0 || failedCount > 0) {
        let message = ''
        if (successCount > 0 && failedCount === 0) {
          message = t('import_success', { count: successCount })
        } else if (successCount === 0 && failedCount > 0) {
          message = t('import_failed', { count: failedCount })
        } else {
          message = t('import_partial_success', {
            success: successCount,
            failed: failedCount,
          })
        }

        if (successCount > 0) {
          toast.success(message)
          booksMutate()
          coversMutate()
        } else {
          toast.error(message)
        }
      }
    }
  }, [importProgress, booksMutate, coversMutate, t])

  if (groups.length) return null
  if (!books) return null

  const allSelected = selectedBookIds.size === books.length
  if (!error) {
    booksMutate()
  }

  const handleImportOperation = async (
    operation: () => Promise<any>,
    setImportProgress: React.Dispatch<
      React.SetStateAction<ImportProgressState>
    >,
    mutate?: () => void,
    fileName?: string,
  ) => {
    try {
      setImportProgress({
        total: 1,
        completed: 0,
        importing: true,
        ...(fileName && {
          currentFile: {
            name: fileName,
            progress: 0,
            index: 0,
          },
        }),
      })

      // ファイル名が指定されている場合は進捗状況を更新する
      if (fileName) {
        // 進捗状況を更新する関数
        const updateProgress = (progress: number) => {
          setImportProgress((prev) => ({
            ...prev,
            currentFile: {
              ...prev.currentFile!,
              progress,
            },
          }))
        }

        // 初期進捗を設定
        updateProgress(10)
      }

      const result = await operation()

      setImportProgress({
        total: 1,
        completed: 1,
        importing: false,
        success: result ? 1 : 0,
        failed: result ? 0 : 1,
      })

      if (mutate) mutate()

      return result
    } catch (error) {
      console.error(t('import_error_log'), error)
      toast.error(t('import_error'))

      setImportProgress({
        total: 1,
        completed: 1,
        importing: false,
        success: 0,
        failed: 1,
      })

      return null
    }
  }

  const handleFileImport = async (
    files: FileList | File[],
    setLoading: React.Dispatch<React.SetStateAction<string | undefined>>,
    setImportProgress: React.Dispatch<
      React.SetStateAction<ImportProgressState>
    >,
  ) => {
    try {
      await handleFiles(files, setLoading, setImportProgress)
    } catch (error) {
      console.error(t('file_import_error_log'), error)
      toast.error(t('import_error'))
      setImportProgress({ total: 0, completed: 0, importing: false })
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

        handleFileImport(e.dataTransfer.files, setLoading, setImportProgress)
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
                      setImportProgress,
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
                      let progressUpdater:
                        | ((progress: number) => void)
                        | undefined
                      setImportProgress((prev) => {
                        if (prev.currentFile) {
                          progressUpdater = (progress) => {
                            setImportProgress((p) => ({
                              ...p,
                              currentFile: {
                                ...p.currentFile!,
                                progress,
                              },
                            }))
                          }
                        }
                        return prev
                      })

                      return await fetchBook(
                        'https://epubtest.org/books/Fundamental-Accessibility-Tests-Basic-Functionality-v1.0.0.epub',
                        (id) => {
                          setLoading(id)
                          if (progressUpdater) {
                            if (id) {
                              progressUpdater(60)
                            } else {
                              progressUpdater(90)
                            }
                          }
                        },
                      )
                    },
                    setImportProgress,
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
                        handleFileImport(files, setLoading, setImportProgress)
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
      <ImportProgress progress={importProgress} />
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
            {books.map((book) =>
              isCoverLoading ? (
                <LoadingBookPlaceholder
                  key={book.id}
                  identifier={book.id}
                  progress={0}
                />
              ) : (
                <Book
                  key={book.id}
                  book={book as any}
                  covers={covers}
                  select={select}
                  selected={has(book.id)}
                  loading={loading === book.id}
                  toggle={toggle}
                />
              ),
            )}
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
