// Design tokens for the literary map (docs/plan.md, section 5.1).
export const tokens = {
  paper: '#e6d9bd',
  ink: '#2b2118',
  inkFaint: 'rgba(43, 33, 24, 0.35)',
} as const

// The story box: where the pipeline resolves names and the base tiles are clipped.
export const storyBounds: [number, number, number, number] = [-113, 27, -104, 36]
