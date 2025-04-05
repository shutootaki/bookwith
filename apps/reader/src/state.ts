import { atom, useAtom } from 'jotai'
import { atomWithStorage } from 'jotai/utils'

import { RenditionSpread } from '@flow/epubjs/types/rendition'

import { IS_SERVER } from './utils'

// function localStorageEffect<T>(key: string, defaultValue: T): AtomEffect<T> {
//   return ({ setSelf, onSet }) => {
//     if (IS_SERVER) return

//     const savedValue = localStorage.getItem(key)
//     if (savedValue === null) {
//       localStorage.setItem(key, JSON.stringify(defaultValue))
//     } else {
//       setSelf(JSON.parse(savedValue))
//     }

//     onSet((newValue, _, isReset) => {
//       isReset
//         ? localStorage.removeItem(key)
//         : localStorage.setItem(key, JSON.stringify(newValue))
//     })
//   }
// }

export const navbarState = atom<boolean>(false)

export interface Settings extends TypographyConfiguration {
  theme?: ThemeConfiguration
}

export interface TypographyConfiguration {
  fontSize?: string
  fontWeight?: number
  fontFamily?: string
  lineHeight?: number
  spread?: RenditionSpread
  zoom?: number
}

interface ThemeConfiguration {
  source?: string
  background?: number
}

export const defaultSettings: Settings = {}

// localStorageを使用したatomの作成
const settingsState = atomWithStorage<Settings>('settings', defaultSettings)

export function useSettings() {
  return useAtom(settingsState)
}
