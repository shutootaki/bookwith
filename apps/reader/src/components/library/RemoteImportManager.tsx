import { Download, Share2 } from 'lucide-react'
import React, { useState } from 'react'

import { TextField } from '..'
import { useTranslation } from '../../hooks'
import { fetchBook } from '../../lib/apiHandler/importHandlers'
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

  return (
    <div className="space-y-2.5">
      <div>
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
                if (el?.reportValidity()) {
                  copy(`${window.location.origin}/?${SOURCE}=${el.value}`)
                }
              },
            },
            {
              title: t('download'),
              Icon: Download,
              disabled: !urlValue.trim(),
              onClick: async (el) => {
                if (el?.reportValidity() && urlValue.trim()) {
                  await handleImportOperation(
                    async () => await fetchBook(el.value, setLoading),
                    onCoverMutate,
                  )
                }
              },
            },
          ]}
        />
      </div>
    </div>
  )
}
