import React, { useEffect, useState } from 'react'
import { useSet } from 'react-use'
import { toast } from 'sonner'

import { useBoolean, useTranslation } from '../../hooks'
import { useLibrary, useBookCovers } from '../../hooks'
import { useLoading } from '../../hooks/useLoading'
import { handleFiles } from '../../lib/apiHandler/importHandlers'
import { cn } from '../../lib/utils'
import { reader, useReaderSnapshot } from '../../models'
import { DropZone } from '../base'
import { Toaster } from '../ui/sonner'

import { BookGrid } from './BookGrid'
import { ImportManager } from './ImportManager'
import { RemoteImportManager } from './RemoteImportManager'
import { SelectionManager } from './SelectionManager'

export const LibraryContainer: React.FC = () => {
  const { books, error, mutate: booksMutate } = useLibrary()
  const { covers, mutate: coversMutate, isCoverLoading } = useBookCovers()

  const [select, toggleSelect] = useBoolean(false)
  const [selectedBookIds, { add, has, toggle, reset }] = useSet<string>()

  const [loading, setLoading] = useState<string | undefined>()

  const { groups } = useReaderSnapshot()
  const t = useTranslation('home')

  const { startLoading, stopLoading, updateProgress, updateSubTasks } =
    useLoading({
      message: t('importing_books'),
      type: 'global',
      showProgress: true,
    })

  useEffect(() => {
    if (!select) reset()
  }, [reset, select])

  if (groups.length) return null
  if (!books) return null

  const allSelected = selectedBookIds.size === books.length
  if (!error) {
    booksMutate()
  }

  const handleImportComplete = () => {
    booksMutate()
    coversMutate()
  }

  const handleFileImport = async (files: FileList | File[]) => {
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
            handleImportComplete()
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

  return (
    <DropZone
      className="scroll-parent h-full p-4"
      onDrop={(e) => {
        const bookId = e.dataTransfer.getData('text/plain')
        const book = books.find((b) => b.id === bookId)
        if (book) reader.addTab(book as any)

        handleFileImport(e.dataTransfer.files)
      }}
    >
      <div className="mb-4 space-y-2.5">
        {select || (
          <RemoteImportManager
            onCoverMutate={coversMutate}
            setLoading={setLoading}
            handleImportOperation={handleImportOperation}
          />
        )}

        <div className={cn(select || 'flex items-center justify-between')}>
          <SelectionManager
            select={!!select}
            selectedBookIds={selectedBookIds}
            allSelected={allSelected}
            onToggleSelect={toggleSelect}
            onSelectAll={() => books.forEach((b) => add(b.id))}
            onDeselectAll={reset}
            onImportComplete={handleImportComplete}
            hasBooks={books.length > 0}
          />
          {select || (
            <ImportManager
              updateProgress={updateProgress}
              handleFileImport={handleFileImport}
              setLoading={setLoading}
              handleImportOperation={handleImportOperation}
              hasBooks={books.length > 0}
              onImportComplete={handleImportComplete}
            />
          )}
        </div>
      </div>

      <BookGrid
        books={books}
        covers={covers}
        select={!!select}
        loading={loading}
        onToggleBook={toggle}
        hasBook={has}
        isCoverLoading={isCoverLoading}
      />

      <Toaster />
    </DropZone>
  )
}
