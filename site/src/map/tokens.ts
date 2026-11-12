// Design tokens for the literary map (docs/plan.md, section 5.1).
export const tokens = {
  paper: '#e4ddcc',
  paperMexico: '#d9cfbb',
  water: '#5f7480',
  ink: '#2b2118',
  inkFaint: 'rgba(43, 33, 24, 0.35)',
  routeWolf: '#4a5560',
  routeBilly: '#6e1f1c',
} as const

// Font stacks: folder names under public/fonts/, built by tiles/build_glyphs.sh.
export const fonts = {
  roman: 'IMFeENrm28P',
  italic: 'IMFeENit28P',
} as const

// Route ink by journey. J2 is Billy's, with the wolf beside him.
export const journeyInk: Record<string, string> = {
  J1: tokens.routeWolf,
  J2: tokens.routeBilly,
}

// The story box: where the pipeline resolves names and the base tiles are clipped.
export const storyBounds: [number, number, number, number] = [-113, 27, -104, 36]
