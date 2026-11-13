// Design tokens for the literary map (docs/plan.md, section 5.1).
export const tokens = {
  paper: '#e4ddcc',
  paperMexico: '#d9cfbb',
  water: '#5f7480',
  ink: '#2b2118',
  inkFaint: 'rgba(43, 33, 24, 0.35)',
  routeWolf: '#4a5560',
  routeBilly: '#6e1f1c',
  routeBoyd: '#2f5d50',
  routeGirl: '#6a3d5c',
} as const

// Font stacks: folder names under public/fonts/, built by tiles/build_glyphs.sh.
export const fonts = {
  roman: 'IMFeENrm28P',
  italic: 'IMFeENit28P',
} as const

// Route ink by journey, after its central figure (plan 5.1): the wolf in slate, Billy in oxblood (J2 with the wolf
// beside him), Boyd in green for the brothers' ride (J4), and "the girl" in plum for the reported J6.
export const journeyInk: Record<string, string> = {
  J1: tokens.routeWolf,
  J2: tokens.routeBilly,
  J3: tokens.routeBilly,
  J4: tokens.routeBoyd,
  J5: tokens.routeBilly,
  J6: tokens.routeGirl,
  J7: tokens.routeBilly,
}

// The story box: where the pipeline resolves names and the base tiles are clipped.
export const storyBounds: [number, number, number, number] = [-113, 27, -104, 36]
