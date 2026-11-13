// Design tokens for the literary map (docs/plan.md, section 5.1): ink on caliche paper. Each colour keeps its place in
// the hierarchy: the Mexico side a shade darker than the paper, the paper above zoom 10 plainer than below,
// the journeys' inks distinct from each other and from the base.
export type Palette = {
  paper: string
  paperMexico: string
  water: string
  // River and creek labels: the water a shade darker, for 4.5:1 against the paper on both sides of the line.
  waterLabel: string
  ink: string
  inkFaint: string
  routeWolf: string
  routeBilly: string
  routeBoyd: string
  routeGirl: string
  // Relief (decision 0016, S5). Below zoom 10: an Imhof tint by elevation (metres, colour) and a chromatic
  // hillshade. From zoom 10: a plain paper by elevation, laid over the paper at 70%, and a light grey hillshade.
  imhof: [number, string][]
  reliefPaper: [string, string]
  // What the paper looks like above the split: the base paper under 70% of reliefPaper. Halos match it.
  paperShown: string
  shadeLow: Shade
  shadeHigh: Shade
  hachure: string
  contour: string
  // Streams in the Raised view, a little fainter than the flat map's water.
  raisedStream: string
}
type Shade = { shadow: string; highlight: string; accent: string }

export const palette: Palette = {
  paper: '#e4ddcc',
  paperMexico: '#d9cfbb',
  water: '#5f7480',
  waterLabel: '#465a65',
  ink: '#2b2118',
  inkFaint: 'rgba(43, 33, 24, 0.35)',
  routeWolf: '#4a5560',
  routeBilly: '#6e1f1c',
  routeBoyd: '#2f5d50',
  routeGirl: '#6a3d5c',
  // Imhof's aerial perspective, adapted to the desert: hazy grey-green basins, pale sand plains, warm ochre on
  // the high sierra, paler summits. The region runs from 0 to about 3,000 m.
  imhof: [[0, '#d3d7c4'], [600, '#dedbbf'], [1100, '#e6dcbb'], [1600, '#e9d9b1'], [1950, '#e0c498'], [2300, '#d3ae88'],
    [2700, '#d8bfa8'], [3200, '#e9e0d6']],
  reliefPaper: ['#f7f4ec', '#f3eee2'],
  paperShown: '#f1ede2',
  // Imhof: blue-violet shadows and warm light; above the split, a light swisstopo grey.
  shadeLow: { shadow: 'rgba(74, 88, 128, 0.5)', highlight: 'rgba(255, 240, 192, 0.35)', accent: 'rgba(74, 88, 128, 0.12)' },
  shadeHigh: { shadow: 'rgba(74, 79, 92, 0.22)', highlight: 'rgba(255, 255, 255, 0.3)', accent: 'rgba(74, 79, 92, 0.05)' },
  hachure: '#6e5443',
  contour: '#b0622e',
  raisedStream: '#6f8796',
}

// Font stacks: folder names under public/fonts/, built by tiles/build_glyphs.sh.
export const fonts = {
  roman: 'IMFeENrm28P',
  italic: 'IMFeENit28P',
} as const

// Route ink by journey, after its central figure (plan 5.1): the wolf in slate, Billy in oxblood (J2 with the wolf
// beside him), Boyd in green for the brothers' ride (J4), and "the girl" in plum for the reported J6.
export function journeyInks(p: Palette): Record<string, string> {
  return { J1: p.routeWolf, J2: p.routeBilly, J3: p.routeBilly, J4: p.routeBoyd, J5: p.routeBilly, J6: p.routeGirl, J7: p.routeBilly }
}

// The sprite sheet of mountain glyphs and vignettes (art/build_sprite.py).
export const SPRITE = 'glyphs'

// The story box: where the pipeline resolves names and the base tiles are clipped.
export const storyBounds: [number, number, number, number] = [-113, 27, -104, 36]
