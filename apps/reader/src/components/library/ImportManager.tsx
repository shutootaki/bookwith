import { Upload } from 'lucide-react'
import React from 'react'

import { Button } from '..'
import { useTranslation } from '../../hooks'
import { fetchBook } from '../../lib/apiHandler/importHandlers'

interface ImportManagerProps {
  onImportComplete: () => void
  setLoading: React.Dispatch<React.SetStateAction<string | undefined>>
  hasBooks: boolean
  handleImportOperation: (
    operation: () => Promise<any>,
    mutate?: () => void,
    fileName?: string,
  ) => Promise<any>
  updateProgress: (progress: number, total: number) => void
  handleFileImport: (files: FileList | File[]) => void
}

export const ImportManager: React.FC<ImportManagerProps> = ({
  onImportComplete,
  setLoading,
  hasBooks,
  handleImportOperation,
  updateProgress,
  handleFileImport,
}) => {
  const t = useTranslation('home')

  return (
    <>
      <div className="flex items-center justify-between gap-4">
        <div className="flex items-center gap-2">
          {!hasBooks && (
            <Button
              variant="secondary"
              size="sm"
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
                  onImportComplete,
                  fileName,
                )
              }}
            >
              {t('download_sample_book')}
            </Button>
          )}
        </div>
      </div>
      <div className="flex items-center gap-2">
        <Button
          variant="default"
          size="sm"
          onClick={() => document.getElementById('file-import')?.click()}
        >
          <Upload className="h-4 w-4" />
          {t('import')}
        </Button>
        <input
          id="file-import"
          type="file"
          accept="application/epub+zip,application/epub,application/zip"
          className="sr-only"
          onChange={async (e) => {
            const files = e.target.files
            if (files) {
              handleFileImport(files)
            }
          }}
          multiple
          aria-label="import-books"
        />
      </div>
    </>
  )
}
