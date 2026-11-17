import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import '../index.css'
import './lab.css'
import LabApp from './LabApp'

// The map lab (site/lab.html): a dev-server page for trying map settings beside the real vintage map.
// `npm run build` leaves it out: index.html is the build's only entry.
createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <LabApp />
  </StrictMode>,
)
