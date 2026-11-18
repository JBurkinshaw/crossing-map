import { afterEach, describe, expect, it, vi } from 'vitest'
import { readFold, synopsisFolded } from './folds'

describe('synopsisFolded', () => {
  it('shows the synopsis of a finished episode in full', () => {
    expect(synopsisFolded('1-09', '1-10')).toBe(false)
  })
  it('folds the synopsis of the episode being read', () => {
    expect(synopsisFolded('1-10', '1-10')).toBe(true)
  })
  it('shows every synopsis once the book is finished', () => {
    expect(synopsisFolded('4-14', '9-99')).toBe(false)
  })
})

describe('readFold', () => {
  afterEach(() => {
    vi.unstubAllGlobals()
  })
  it('starts closed with nothing stored', () => {
    vi.stubGlobal('localStorage', { getItem: () => null })
    expect(readFold('k')).toBe(false)
  })
  it('opens when the reader left it open', () => {
    vi.stubGlobal('localStorage', { getItem: (k: string) => (k === 'k' ? 'open' : null) })
    expect(readFold('k')).toBe(true)
  })
  it('starts closed when storage is blocked', () => {
    vi.stubGlobal('localStorage', {
      getItem: () => {
        throw new Error('blocked')
      },
    })
    expect(readFold('k')).toBe(false)
  })
})
