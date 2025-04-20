import { useRouter } from 'next/router'
import { useCallback } from 'react'

import locales from '../../locales'

export function useTranslation(scope?: string) {
  const { locale = 'en-US' } = useRouter()

  return useCallback(
    (key: string, params?: Record<string, any>) => {
      const localeData =
        locale in locales
          ? (locales as any)[locale]
          : (locales as any)['en-US'] || {}

      const translationKey = scope ? `${scope}.${key}` : key
      let text = translationKey in localeData ? localeData[translationKey] : key

      if (params && text) {
        Object.entries(params).forEach(([paramKey, value]) => {
          text = text.replace(new RegExp(`{${paramKey}}`, 'g'), String(value))
        })
      }

      return text
    },
    [locale, scope],
  )
}
