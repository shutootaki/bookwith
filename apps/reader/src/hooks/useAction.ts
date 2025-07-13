import { atom, useAtom, useSetAtom } from 'jotai'

export type Action =
  | 'toc'
  | 'chat'
  | 'search'
  | 'annotation'
  | 'typography'
  | 'image'
  | 'timeline'
  | 'theme'
  | 'podcast'

export const actionState = atom<Action | undefined>(undefined)

export function useSetAction() {
  return useSetAtom(actionState)
}

export function useAction() {
  return useAtom(actionState)
}
