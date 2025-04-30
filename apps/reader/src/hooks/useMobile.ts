import { atom, useAtom } from 'jotai'
import { useEffect } from 'react'

export const mobileState = atom<boolean | undefined>(undefined)

let listened = false

export function useMobile() {
  const [mobile, setMobile] = useAtom(mobileState)

  useEffect(() => {
    if (listened) return
    listened = true

    const mq = window.matchMedia('(max-width: 640px)')
    setMobile(mq.matches)
    mq.addEventListener('change', (e) => {
      setMobile(e.matches)
    })
  }, [setMobile])

  return mobile
}
