import { Upload } from 'lucide-react'
import React from 'react'

import { Button } from '..'
import { useTranslation } from '../../hooks'

interface ImportManagerProps {
  handleFileImport: (files: FileList | File[]) => void
}

// 旧: 第三者ホスト epubtest.org からサンプル EPUB を直接ダウンロードする UI を提供していたが、
// レビュー文書の LOW 指摘（外部ホストの改竄時に CR-5 と合わせた 1-click XSS の入口になり得る）
// を受けて削除済み。サンプル EPUB が必要な場合は自前ホスト（cdn.bookwith.app 等）の URL を
// `RemoteImportManager` に渡す経路を使う（CR-7 の allow-list が適用される）。
export const ImportManager: React.FC<ImportManagerProps> = ({ handleFileImport }) => {
  const t = useTranslation('home')

  return (
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
  )
}
