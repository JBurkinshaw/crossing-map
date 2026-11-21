import { afterEach, describe, expect, it, vi } from 'vitest'
import { readChoice } from './storage'

const VIEWS = ['flat', 'tilted', 'oblique'] as const

describe('readChoice', () => {
  afterEach(() => {
    vi.unstubAllGlobals()
  })
  it('gives the fallback with nothing stored', () => {
    vi.stubGlobal('localStorage', { getItem: () => null })
    expect(readChoice('k', VIEWS, 'flat')).toBe('flat')
  })
  it('gives the stored choice', () => {
    vi.stubGlobal('localStorage', { getItem: (k: string) => (k === 'k' ? 'oblique' : null) })
    expect(readChoice('k', VIEWS, 'flat')).toBe('oblique')
  })
  it('gives the fallback for a choice no longer offered', () => {
    vi.stubGlobal('localStorage', { getItem: () => 'raised' })
    expect(readChoice('k', VIEWS, 'flat')).toBe('flat')
  })
})
