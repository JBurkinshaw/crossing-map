import { afterEach, describe, expect, it, vi } from 'vitest'

// A browser at a reader's stop, arriving from a search engine.
function browser() {
  const sendBeacon = vi.fn((_url: string) => true)
  vi.stubGlobal('navigator', { sendBeacon, webdriver: false })
  vi.stubGlobal('document', { referrer: 'https://search.example/' })
  vi.stubGlobal('window', { screen: { width: 1280 }, location: { hash: '#stop=j1-cloverdale-creek&map=9/31.4/-108.9' } })
  return sendBeacon
}

const sent = (sendBeacon: ReturnType<typeof browser>) => sendBeacon.mock.calls.map(([url]) => new URL(url))

afterEach(() => {
  vi.unstubAllGlobals()
  vi.unstubAllEnvs()
  vi.resetModules()
})

describe('counting visits', () => {
  it('sends nothing from a build with no site code', async () => {
    vi.stubEnv('VITE_GOATCOUNTER', '')
    const sendBeacon = browser()
    const { COUNTING, countPage, countEvent } = await import('./analytics')
    countPage('/about')
    countEvent('read-on')
    expect(COUNTING).toBe(false)
    expect(sendBeacon).not.toHaveBeenCalled()
  })

  it('sends the route and never the hash', async () => {
    vi.stubEnv('VITE_GOATCOUNTER', 'example')
    const sendBeacon = browser()
    const { countPage, countEvent } = await import('./analytics')
    countPage('/')
    countEvent('view-oblique')
    const [page, event] = sent(sendBeacon)
    expect(page.origin + page.pathname).toBe('https://example.goatcounter.com/count')
    expect(Object.fromEntries(page.searchParams)).toMatchObject({ p: '/', s: '1280', r: 'https://search.example/' })
    expect(Object.fromEntries(event.searchParams)).toMatchObject({ p: 'view-oblique', e: 'true' })
    for (const url of [page, event]) expect(url.href).not.toMatch(/stop|map=|cloverdale|%23/)
  })

  it('does not fail in a browser with no sendBeacon, or one that throws', async () => {
    vi.stubEnv('VITE_GOATCOUNTER', 'example')
    browser()
    const { countPage } = await import('./analytics')
    vi.stubGlobal('navigator', { webdriver: false })
    expect(() => countPage('/')).not.toThrow()
    vi.stubGlobal('navigator', {
      webdriver: false,
      sendBeacon: () => {
        throw new Error('blocked')
      },
    })
    expect(() => countPage('/')).not.toThrow()
  })

  it('sends nothing from an automated browser', async () => {
    vi.stubEnv('VITE_GOATCOUNTER', 'example')
    const sendBeacon = browser()
    vi.stubGlobal('navigator', { sendBeacon, webdriver: true })
    const { countPage } = await import('./analytics')
    countPage('/')
    expect(sendBeacon).not.toHaveBeenCalled()
  })
})
