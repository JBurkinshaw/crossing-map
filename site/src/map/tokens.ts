// Design tokens for the literary map (docs/plan.md, section 5.1), in two themes: ink on caliche paper, and
// "by lamplight", the same lines in a warm light ink on a near-black paper. Each colour keeps its place in
// the hierarchy: the Mexico side a shade darker than the paper, the paper above zoom 10 plainer than below,
// the journeys' inks distinct from each other and from the base.
export type Theme = 'light' | 'lamplight'

export type Palette = {
  paper: string
  paperMexico: string
  water: string
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

export const palettes: Record<Theme, Palette> = {
  light: {
    paper: '#e4ddcc',
    paperMexico: '#d9cfbb',
    water: '#5f7480',
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
  },
  lamplight: {
    paper: '#1d1915',
    paperMexico: '#16130f',
    water: '#8ea6b3',
    ink: '#e6d9c0',
    inkFaint: 'rgba(230, 217, 192, 0.35)',
    routeWolf: '#9cadbd',
    routeBilly: '#d97a6c',
    routeBoyd: '#7fb8a2',
    routeGirl: '#c99bc0',
    // The same aerial perspective in the dark: deep grey-green basins, dark sand plains, umber on the high
    // sierra, the summits a little lighter, as if the lamp catches them.
    imhof: [[0, '#1b201c'], [600, '#21221b'], [1100, '#26241b'], [1600, '#2b2619'], [1950, '#32291a'], [2300, '#3a2d1f'],
      [2700, '#3a312a'], [3200, '#3f3b36']],
    reliefPaper: ['#141210', '#161411'],
    paperShown: '#171512',
    // Shadows sink towards black, blue below the split; the light is the lamp's, faint and warm.
    shadeLow: { shadow: 'rgba(4, 6, 18, 0.55)', highlight: 'rgba(255, 214, 150, 0.1)', accent: 'rgba(4, 6, 18, 0.15)' },
    shadeHigh: { shadow: 'rgba(0, 0, 0, 0.45)', highlight: 'rgba(255, 236, 200, 0.12)', accent: 'rgba(0, 0, 0, 0.1)' },
    // Light lines on dark paper read stronger than dark on light at the same contrast, so the relief's sepia
    // and orange-brown sit a little under their light-theme contrast with the paper, to stay behind the story.
    hachure: '#9a846f',
    contour: '#a9683f',
    raisedStream: '#687f8b',
  },
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

// The sprite sheet of mountain glyphs and vignettes for each theme (art/build_sprite.py): the drawings' paper
// fill, which knocks out the hachures behind them, is the theme's paper.
export const spriteName: Record<Theme, string> = { light: 'glyphs', lamplight: 'glyphs-lamplight' }

// The story box: where the pipeline resolves names and the base tiles are clipped.
export const storyBounds: [number, number, number, number] = [-113, 27, -104, 36]
