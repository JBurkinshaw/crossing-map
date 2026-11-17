import { useEffect, useRef } from 'react'
import type { IControl } from 'maplibre-gl'
import { useControl } from '@vis.gl/react-maplibre'

// The Home button (design section 9), under the zoom buttons: it frames the whole journey in focus. A house says
// "home page" to many readers, so the icon is a frame around a winding route, and the title names the action.
class HomeButton implements IControl {
  private box = document.createElement('div')
  constructor(onClick: () => void) {
    this.box.className = 'maplibregl-ctrl maplibregl-ctrl-group'
    const button = document.createElement('button')
    button.type = 'button'
    button.className = 'home-button'
    button.title = 'Zoom to the current journey'
    button.setAttribute('aria-label', 'Zoom to the current journey')
    button.innerHTML =
      '<svg viewBox="0 0 20 20" width="18" height="18" aria-hidden="true" fill="none" stroke="currentColor">' +
      '<path d="M2.5 7 V2.5 H7 M13 2.5 H17.5 V7 M17.5 13 V17.5 H13 M7 17.5 H2.5 V13" stroke-width="1.6"/>' +
      '<path d="M6 14 C8 12 7 9 10 8.5 S12.5 6 14 6" stroke-width="1.4" stroke-dasharray="2.2 1.4"/></svg>'
    button.addEventListener('click', onClick)
    this.box.append(button)
  }
  onAdd() {
    return this.box
  }
  onRemove() {
    this.box.remove()
  }
}

export function HomeControl({ onHome }: { onHome: () => void }) {
  // The control is made once; the ref keeps its click on the latest handler.
  const latest = useRef(onHome)
  useEffect(() => {
    latest.current = onHome
  })
  useControl(() => new HomeButton(() => latest.current()), { position: 'top-left' })
  return null
}
