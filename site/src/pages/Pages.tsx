import { useEffect, useRef } from 'react'
import { mapHref, type Route } from '../route'
import { About } from './About'
import { Credits } from './Credits'
import { Data } from './Data'
import { HowItsBuilt } from './HowItsBuilt'

const PAGES: { route: Exclude<Route, '/'>; label: string; title: string }[] = [
  { route: '/about', label: 'About', title: 'About this map' },
  { route: '/about/how-its-built', label: "How it's built", title: "How it's built" },
  { route: '/data', label: 'Data', title: 'The data' },
  { route: '/credits', label: 'Credits', title: 'Credits' },
]

// The site's pages, over the map (which stays loaded underneath, so returning to it is instant).
// Loaded as their own chunk the first time a page opens.
export default function Pages({ route }: { route: Exclude<Route, '/'> }) {
  const page = PAGES.find((p) => p.route === route)!
  const scroller = useRef<HTMLDivElement>(null)
  const heading = useRef<HTMLHeadingElement>(null)
  useEffect(() => {
    document.title = `${page.title} · The Crossing: a reading map`
    scroller.current?.scrollTo(0, 0)
    heading.current?.focus()
    return () => {
      document.title = 'The Crossing: a reading map'
    }
  }, [page])

  // The map and panel stay loaded under the page, out of reach of the keyboard and screen readers.
  useEffect(() => {
    const others = [...(scroller.current?.parentElement?.children ?? [])].filter((el) => el !== scroller.current)
    for (const el of others) el.setAttribute('inert', '')
    return () => others.forEach((el) => el.removeAttribute('inert'))
  }, [])

  return (
    <div className="page" ref={scroller}>
      <header className="page-header">
        {/* The camera is read on click: on a page opened directly, the map writes it only once it has framed the journey. */}
        <a
          className="page-home"
          href={mapHref()}
          onClick={(e) => {
            e.preventDefault()
            window.location.hash = mapHref()
          }}
        >
          ← The map
        </a>
        <nav aria-label="Pages">
          {PAGES.map((p) => (
            <a key={p.route} href={`#${p.route}`} aria-current={p.route === route ? 'page' : undefined}>
              {p.label}
            </a>
          ))}
        </nav>
      </header>
      <article className="page-body">
        <h1 ref={heading} tabIndex={-1}>
          {page.title}
        </h1>
        {route === '/about' && <About />}
        {route === '/about/how-its-built' && <HowItsBuilt />}
        {route === '/data' && <Data />}
        {route === '/credits' && <Credits />}
      </article>
    </div>
  )
}
