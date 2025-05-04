import { atom, useAtom } from 'jotai'
import { atomWithStorage } from 'jotai/utils'

import { RenditionSpread } from '@flow/epubjs/types/rendition'

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

const settingsState = atomWithStorage<Settings>('settings', defaultSettings)

export function useSettings() {
  return useAtom(settingsState)
}
