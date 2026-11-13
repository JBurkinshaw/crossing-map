import { useSyncExternalStore } from 'react'

// The width below which the panel becomes the drawer; index.css uses the same.
const PHONE = '(max-width: 720px)'
const phoneQuery = () => window.matchMedia(PHONE)
export function usePhone(): boolean {
  return useSyncExternalStore(
    (onChange) => {
      const q = phoneQuery()
      q.addEventListener('change', onChange)
      return () => q.removeEventListener('change', onChange)
    },
    () => phoneQuery().matches,
  )
}
