import { Download, Share2 } from 'lucide-react'
import React, { useState } from 'react'

import { TextField } from '..'
import { useTranslation } from '../../hooks'
import {
  RemoteImportError,
  fetchBook,
  isAllowedRemoteImportUrl,
} from '../../lib/apiHandler/importHandlers'
import { copy } from '../../utils/utils'

const SOURCE = 'src'

interface RemoteImportManagerProps {
  onCoverMutate?: () => void
  setLoading: React.Dispatch<React.SetStateAction<string | undefined>>
  handleImportOperation: (
    operation: () => Promise<any>,
    mutate?: () => void,
    fileName?: string,
  ) => Promise<any>
}

export const RemoteImportManager: React.FC<RemoteImportManagerProps> = ({
  onCoverMutate,
  setLoading,
  handleImportOperation,
}) => {
  const t = useTranslation('home')

  const [urlValue, setUrlValue] = useState('')

  // CR-7: TextField の入力値を信頼ホスト allow-list で検証。失敗時は alert を出して null を返す。
  const validatedUrl = (
    el: HTMLInputElement | null | undefined,
    rejectMessage: string,
  ): string | null => {
    if (!el?.reportValidity()) return null
    if (!isAllowedRemoteImportUrl(el.value)) {
      window.alert(rejectMessage)
      return null
    }
    return el.value
  }

  return (
    <div className="space-y-2.5">
      <TextField
        name={SOURCE}
        placeholder={t('remote_epub_placeholder')}
        type="url"
        hideLabel
        value={urlValue}
        onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
          setUrlValue(e.target.value)
        }
        actions={[
          {
            title: t('share'),
            Icon: Share2,
            onClick(el) {
              const url = validatedUrl(
                el,
                'This URL is not on the trusted import host list and cannot be shared.',
              )
              if (!url) return
              const shareUrl = new URL('/', window.location.origin)
              shareUrl.searchParams.set(SOURCE, url)
              copy(shareUrl.toString())
            },
          },
          {
            title: t('download'),
            Icon: Download,
            disabled: !urlValue.trim(),
            onClick: async (el) => {
              if (!urlValue.trim()) return
              const url = validatedUrl(
                el,
                'This URL is not on the trusted import host list.',
              )
              if (!url) return
              if (!window.confirm(`Import EPUB from this URL?\n\n${url}`)) {
                return
              }
              try {
                await handleImportOperation(
                  async () => await fetchBook(url, setLoading),
                  onCoverMutate,
                )
              } catch (err) {
                if (err instanceof RemoteImportError) {
                  window.alert(err.message)
                } else {
                  console.error(err)
                }
              }
            },
          },
        ]}
      />
    </div>
  )
}
