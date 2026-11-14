import { useSyncExternalStore } from 'react'
import { PHONE_QUERY } from '../map/setup'

const phoneQuery = () => window.matchMedia(PHONE_QUERY)
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
