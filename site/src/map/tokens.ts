import type { ExpressionSpecification } from 'maplibre-gl'

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
  // Lakes, opaque because they lie over the rivers: the water at 25% over the paper, and 12% for intermittent
  // ones.
  lake: string
  lakeDry: string
  ink: string
  inkFaint: string
  // One ink per journey (decision 0033).
  journeys: Record<string, string>
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
  // Streams in the Oblique view, a little fainter than the flat map's water.
  // The water between an Oblique river's two inked banks (decision 0034, after Owens's comic-book rivers).
  obliqueWater: string
  // Land cover (decision 0034), by crossing.landcover's classes: school-atlas tints mixed 60% over paperShown,
  // opaque so that neighbouring polygons show no seam.
  landcover: Record<LandCover, string>
}
export type LandCover = 'water' | 'riparian' | 'pine' | 'oak' | 'grass' | 'scrub' | 'fields' | 'town'
// The order the layer key lists them in.
export const LAND_COVERS: { id: LandCover; label: string }[] = [
  { id: 'pine', label: 'Pine forest' },
  { id: 'oak', label: 'Oak woodland' },
  { id: 'riparian', label: 'Gallery forest and wetland' },
  { id: 'grass', label: 'Grassland' },
  { id: 'scrub', label: 'Desert scrub' },
  { id: 'fields', label: 'Fields' },
  { id: 'town', label: 'Towns' },
  { id: 'water', label: 'Water' },
]
type Shade = { shadow: string; highlight: string; accent: string }

export const palette: Palette = {
  paper: '#efe5c8',
  paperMexico: '#e6d9b9',
  water: '#5f7480',
  waterLabel: '#465a65',
  lake: '#cbc9b6',
  lakeDry: '#ded7bf',
  ink: '#2b2118',
  inkFaint: 'rgba(43, 33, 24, 0.35)',
  // The hand-coloured tints of the Mitchell and Gray atlas maps, and the red route of the Trail of Blood Meridian
  // for J2. Each is at least 3.2:1 against the paper and at least 12 apart (OKLab distance x100) from the others.
  journeys: {
    J1: '#2e4a8a', // indigo
    J2: '#c0391b', // vermilion
    J3: '#6e1f1c', // oxblood
    J4: '#2f6f2a', // sap green
    J5: '#a8740c', // ochre
    J6: '#8a4fb0', // violet
    J7: '#b8457f', // rose madder
  },
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
  obliqueWater: '#8fb3c4',
  // Blue water, bright green gallery forest, sage pine, olive oak, straw grass, adobe scrub, yellow-green fields
  // and brick towns: #9cc3d3, #7fae63, #86a26c, #b3bf80, #ecdc98, #e3c39b, #c9d27c and #d4876a before the mix.
  landcover: {
    water: '#c0d4d3', riparian: '#aec790', pine: '#b2c095', oak: '#cdd1a1',
    grass: '#f0e3b0', scrub: '#ead4b1', fields: '#dbdd9f', town: '#e1b094',
  },
}

// Font stacks: folder names under public/fonts/, built by tiles/build_glyphs.sh.
export const fonts = {
  roman: 'IMFeENrm28P',
  italic: 'IMFeENit28P',
  smallCaps: 'IMFeENsc28P',
} as const

// The type scale after the Wheeler sheets (review/stage-9/wheeler-type/README.md; decision 0027): sizes in px at
// zoom 11, all in the one ink. The spot height is the unit; towns are about 1.4 times it, in roman (the larger,
// places.geojson's cities, in capitals); ranches, stations and springs about the unit, in quiet italic; passes
// about the unit, in small capitals. Landform names along their axes (relief.ts) are about twice it.
export const typeScale = { spot: 10.5, town: 14.5, quiet: 10.5, pass: 10.5 } as const
// Quiet names (ranches, stations, springs) are in the same ink at this opacity.
export const QUIET_OPACITY = 0.72
// A size at zoom 11 grown with the zoom, less than the ground grows: 0.85 of it at zoom 9 and below, 1.15 at 13.
export const zoomedSize = (size: number): ExpressionSpecification => ['interpolate', ['linear'], ['zoom'], 9, size * 0.85, 11, size, 13, size * 1.15]

// Route ink by journey (design 5.1, decision 0033): one ink each, so the journeys tell apart at a glance.
export function journeyInks(p: Palette): Record<string, string> {
  return p.journeys
}

// How sure a route line is, drawn as a dash pattern (decision 0033): solid where the book names the road or river,
// long dashes for a modelled path, sparse short dashes for a curve that only joins the stops. Widths in px with the
// journey in focus; dashes in px, divided by the width for MapLibre, whose dash arrays are in line widths.
export const routeLines = {
  traced: { width: 3.5, dash: null },
  modeled: { width: 3, dash: [12, 6] },
  curve: { width: 2, dash: [4, 6], opacity: 0.75 },
} as const
// A route out of focus is drawn at this share of its width.
export const OUT_OF_FOCUS_WIDTH = 0.5
// A dash pattern in line widths, for MapLibre's line-dasharray.
export const dashInWidths = (dash: readonly number[], width: number): number[] => dash.map((d) => d / width)

// The sprite sheet of mountain glyphs and vignettes (art/build_sprite.py).
export const SPRITE = 'glyphs'

// The story box: where the pipeline resolves names and the base tiles are clipped.
export const storyBounds: [number, number, number, number] = [-113, 27, -104, 36]
