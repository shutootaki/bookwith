import { useCallback, useState } from 'react'

export function useBoolean(
  initial?: boolean,
): readonly [boolean | undefined, (v?: any) => void] {
  const [state, setState] = useState(initial)
  const toggle = useCallback((v?: any) => {
    setState((s) => {
      if (typeof v === 'boolean') {
        return v
      }
      return !s
    })
  }, [])
  return [state, toggle]
}
