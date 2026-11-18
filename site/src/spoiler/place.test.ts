import { afterEach, describe, expect, it, vi } from 'vitest'
import { savedPlaces, savePlace } from './place'

// A browser's address and storage, enough for spoiler/place.ts and the hash helpers in route.ts.
function stubBrowser(hash: string, stored: Record<string, string> = {}) {
  const location = { hash }
  vi.stubGlobal('window', { location })
  vi.stubGlobal('history', { state: null, replaceState: (_: unknown, __: string, url: string) => (location.hash = url) })
  vi.stubGlobal('localStorage', { getItem: (k: string) => stored[k] ?? null, setItem: (k: string, v: string) => (stored[k] = v) })
  return { location, stored }
}

describe('savedPlaces', () => {
  afterEach(() => {
    vi.unstubAllGlobals()
  })
  it('puts the link before the last visit', () => {
    stubBrowser('#map=8/31/-108&stop=j2-b', { 'crossing-map.place': 'j1-a' })
    expect(savedPlaces()).toEqual(['j2-b', 'j1-a'])
  })
  it('has nothing on a first visit', () => {
    stubBrowser('')
    expect(savedPlaces()).toEqual([])
  })
})

describe('savePlace', () => {
  afterEach(() => {
    vi.unstubAllGlobals()
  })
  it('stores the stop and puts it in the address beside the camera', () => {
    const { location, stored } = stubBrowser('#map=8/31/-108&stop=j1-a')
    savePlace('j2-b')
    expect(location.hash).toBe('#map=8/31/-108&stop=j2-b')
    expect(stored['crossing-map.place']).toBe('j2-b')
  })
  it('keeps a page route first', () => {
    const { location } = stubBrowser('#/about&map=8/31/-108')
    savePlace('j2-b')
    expect(location.hash).toBe('#/about&map=8/31/-108&stop=j2-b')
  })
  it('starts the hash when there is none', () => {
    const { location } = stubBrowser('')
    savePlace('j2-b')
    expect(location.hash).toBe('#stop=j2-b')
  })
})
