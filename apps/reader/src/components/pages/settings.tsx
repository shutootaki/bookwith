import Dexie from 'dexie'
import { useRouter } from 'next/router'
import { PropsWithChildren } from 'react'

import { ColorScheme, useColorScheme, useTranslation } from '@flow/reader/hooks'

import { Button } from '../Button'
import { Select } from '../Form'
import { Page } from '../Page'

export const Settings: React.FC = () => {
  const { scheme, setScheme } = useColorScheme()
  const { asPath, push, locale } = useRouter()
  const t = useTranslation('settings')

  return (
    <Page headline={t('title')}>
      <div className="space-y-6">
        <Item title={t('language')}>
          <Select
            value={locale}
            onChange={(e) => {
              push(asPath, undefined, { locale: e.target.value })
            }}
          >
            <option value="en-US">{t('language.english')}</option>
            <option value="ja-JP">{t('language.japanese')}</option>
            <option value="cmn-CN">{t('language.chinese')}</option>
          </Select>
        </Item>
        <Item title={t('color_scheme')}>
          <Select
            value={scheme}
            onChange={(e) => {
              setScheme(e.target.value as ColorScheme)
            }}
          >
            <option value="system">{t('color_scheme.system')}</option>
            <option value="light">{t('color_scheme.light')}</option>
            <option value="dark">{t('color_scheme.dark')}</option>
          </Select>
        </Item>
        <Item title={t('cache')}>
          <Button
            variant="secondary"
            onClick={() => {
              // M-16: 確認ダイアログ + bookwith 名前空間に限定して削除する。
              if (
                !window.confirm(
                  'Clear BookWith local cache? This removes downloaded books and chats stored on this device.',
                )
              ) {
                return
              }
              try {
                // localStorage は bookwith.* / flow-* を対象にする（他アプリの値を巻き込まない）
                const keysToDelete: string[] = []
                for (let i = 0; i < window.localStorage.length; i++) {
                  const k = window.localStorage.key(i)
                  if (!k) continue
                  if (
                    k.startsWith('bookwith.') ||
                    k.startsWith('flow-') ||
                    k === 'reader' ||
                    k === 'sw-cache-version'
                  ) {
                    keysToDelete.push(k)
                  }
                }
                keysToDelete.forEach((k) => window.localStorage.removeItem(k))
              } catch (e) {
                console.warn('Failed to clear local storage subset:', e)
              }
              Dexie.getDatabaseNames().then((names) => {
                names
                  .filter(
                    (n) => n.startsWith('bookwith') || n.startsWith('flow'),
                  )
                  .forEach((n) => Dexie.delete(n))
              })
            }}
          >
            {t('cache.clear')}
          </Button>
        </Item>
      </div>
    </Page>
  )
}

interface PartProps {
  title: string
}
const Item: React.FC<PropsWithChildren<PartProps>> = ({ title, children }) => {
  return (
    <div>
      <h3 className="typescale-title-small text-on-surface-variant">{title}</h3>
      <div className="mt-2">{children}</div>
    </div>
  )
}

Settings.displayName = 'settings'
