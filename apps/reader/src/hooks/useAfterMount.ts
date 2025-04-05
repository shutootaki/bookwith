import { useEffect, useState } from 'react'

function useMounted() {
  const [mounted, setMounted] = useState(false)
  useEffect(() => {
    setMounted(true)
    return () => setMounted(false)
  }, [])
  return mounted
}

export function useAfterMount<T>(v: T) {
  return useMounted() ? v : null
}
