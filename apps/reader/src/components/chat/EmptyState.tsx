import React from 'react'

import { useTranslation } from '@flow/reader/hooks'

export const EmptyState: React.FC = () => {
  const t = useTranslation()

  return (
    <div className="flex h-full flex-col justify-center px-2 text-center text-gray-500">
      <div className="mb-4">
        <svg
          className="mx-auto h-12 w-12"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={1.5}
            d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"
          />
        </svg>
      </div>
      <h3 className="text-lg font-medium">{t('chat.empty_title')}</h3>
      <p className="text-sm">{t('chat.empty_description')}</p>
    </div>
  )
}
