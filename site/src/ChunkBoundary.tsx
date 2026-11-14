import { Component, type ReactNode } from 'react'

// Catches a lazily loaded chunk that fails to load, such as a tab left open across a redeploy whose old chunk
// file is gone, so one missing chunk does not unmount the whole app.
type Props = { children: ReactNode; fallback?: ReactNode; onError?: () => void }

export class ChunkBoundary extends Component<Props, { failed: boolean }> {
  state = { failed: false }

  static getDerivedStateFromError() {
    return { failed: true }
  }

  componentDidCatch() {
    this.props.onError?.()
  }

  render() {
    return this.state.failed ? (this.props.fallback ?? null) : this.props.children
  }
}
