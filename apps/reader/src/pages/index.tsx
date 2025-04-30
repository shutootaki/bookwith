import clsx from 'clsx'
import Head from 'next/head'
import { useRouter } from 'next/router'
import React, { useEffect, useState } from 'react'
import {
  MdCheckBox,
  MdCheckBoxOutlineBlank,
  MdOutlineFileDownload,
  MdOutlineShare,
} from 'react-icons/md'
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

import { ReaderGridView, Button, TextField, DropZone } from '../components'
import ImportProgress, {
  ImportProgressState,
} from '../components/ImportProgress'
import { Toaster } from '../components/ui/sonner'
import { fetchBook, handleFiles, deleteBooksFromAPI } from '../file'
import { useBoolean } from '../hooks'
import {
  useDisablePinchZooming,
  useLibrary,
  useMobile,
  useRemoteCovers,
  useTranslation,
} from '../hooks'
import { CoversResponse } from '../hooks/useLibrary'
import { reader, useReaderSnapshot } from '../models'
import { lock } from '../styles'
import { copy } from '../utils'
import { components } from '../lib/openapi-schema/schema'

const placeholder = `data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1 1"><rect fill="gray" fill-opacity="0" width="1" height="1"/></svg>`

const SOURCE = 'src'

export default function Index() {
  const { focusedTab } = useReaderSnapshot()
  const router = useRouter()
  const src = new URL(window.location.href).searchParams.get(SOURCE)
  const [loading, setLoading] = useState(!!src)

  useDisablePinchZooming()

  useEffect(() => {
    let src = router.query[SOURCE]
    if (!src) return
    if (!Array.isArray(src)) src = [src]

    Promise.all(
      src.map((s) =>
        fetchBook(s).then((b) => {
          if (b) reader.addTab(b as any)
        }),
      ),
    ).finally(() => setLoading(false))
  }, [router.query])

  useEffect(() => {
    if ('launchQueue' in window && 'LaunchParams' in window) {
      window.launchQueue.setConsumer((params) => {
        if (params.files.length) {
          Promise.all(params.files.map((f) => f.getFile()))
            .then((files) => handleFiles(files))
            .then((result) => {
              if (result && 'newBooks' in result) {
                result.newBooks.forEach((b: any) => reader.addTab(b))
              }
            })
        }
      })
    }
  }, [])

  useEffect(() => {
    router.beforePopState(({ url }) => {
      if (url === '/') {
        reader.clear()
      }
      return true
    })
  }, [router])

  return (
    <>
      <Head>
        {/* https://github.com/microsoft/vscode/blob/36fdf6b697cba431beb6e391b5a8c5f3606975a1/src/vs/code/browser/workbench/workbench.html#L16 */}
        {/* Disable pinch zooming */}
        <meta
          name="viewport"
          content="width=device-width, initial-scale=1.0, maximum-scale=1.0, minimum-scale=1.0, user-scalable=no"
        />
        <title>{focusedTab?.title ?? 'Bookwith'}</title>
      </Head>
      <ReaderGridView />
      {loading || <Library />}
    </>
  )
}

const Library: React.FC = () => {
  const { books, error, mutate: booksMutate } = useLibrary()
  const { covers, mutate: coversMutate } = useRemoteCovers()
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
                      // 進捗状態を追跡する関数を作成
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
                          // ローディング状態に応じて進捗を更新
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
            />
          ))}
        </ul>
      </div>
      <Toaster />
    </DropZone>
  )
}

interface BookProps {
  book: components['schemas']['BookDetail']
  covers?: CoversResponse
  select?: boolean
  selected?: boolean
  loading?: boolean
  toggle: (id: string) => void
}
const Book: React.FC<BookProps> = ({
  book,
  covers,
  select,
  selected,
  loading,
  toggle,
}) => {
  const router = useRouter()
  const mobile = useMobile()

  const coverData = covers?.data?.find((c) => c.book_id === book.id)
  const cover = coverData?.cover_url

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
