// Design tokens for the literary map (docs/design.md, section 5.1): ink on cream paper, after the Wheeler Survey's
// sheet 70A (1877; review/stage-8/wheeler/README.md). Each colour keeps its place in
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
  // Relief (decisions 0016 and 0025). Below zoom 10: an Imhof tint by elevation (metres, colour) and a MapTiler-like
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
  paper: '#efe5c8',
  paperMexico: '#e6d9b9',
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
  reliefPaper: ['#f8f0d8', '#f4ead0'],
  paperShown: '#f5edd3',
  // MapTiler Topo's hillshade colours (its topo-v4 style: hsl(0, 0%, 50%), hsl(51, 12%, 83%), hsl(51, 67%, 56%)),
  // the same either side of the zoom fade (decision 0025).
  shadeLow: { shadow: 'rgba(128, 128, 128, 1)', highlight: 'rgba(217, 214, 206, 1)', accent: 'rgba(218, 193, 68, 1)' },
  shadeHigh: { shadow: 'rgba(128, 128, 128, 1)', highlight: 'rgba(217, 214, 206, 1)', accent: 'rgba(218, 193, 68, 1)' },
  // Wheeler's brown-black (his darkest ink, #110600 to #221802, lifted a little for the screen).
  hachure: '#2e2010',
  contour: '#b0622e',
  raisedStream: '#6f8796',
}

// Font stacks: folder names under public/fonts/, built by tiles/build_glyphs.sh.
export const fonts = {
  roman: 'IMFeENrm28P',
  italic: 'IMFeENit28P',
  smallCaps: 'IMFeENsc28P',
} as const

// Route ink by journey, after its central figure (design 5.1): the wolf in slate, Billy in oxblood (J2 with the wolf
// beside him), Boyd in green for the brothers' ride (J4), and "the girl" in plum for the reported J6.
export function journeyInks(p: Palette): Record<string, string> {
  return { J1: p.routeWolf, J2: p.routeBilly, J3: p.routeBilly, J4: p.routeBoyd, J5: p.routeBilly, J6: p.routeGirl, J7: p.routeBilly }
}

// The sprite sheet of mountain glyphs and vignettes (art/build_sprite.py).
export const SPRITE = 'glyphs'

// The story box: where the pipeline resolves names and the base tiles are clipped.
export const storyBounds: [number, number, number, number] = [-113, 27, -104, 36]
