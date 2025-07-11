import { Theme } from '@material/material-color-utilities'
import { atom, useAtomValue, useSetAtom } from 'jotai'

const themeState = atom<Theme | undefined>(undefined)

export function useTheme() {
  return useAtomValue(themeState)
}

export function useSetTheme() {
  return useSetAtom(themeState)
}
