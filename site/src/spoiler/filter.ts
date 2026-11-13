import type { Feature, FeatureCollection, GeoJsonProperties, Geometry } from 'geojson'
import type { ExpressionSpecification, FilterSpecification, StyleSpecification } from 'maplibre-gl'
import type { Story } from '../data/story'

// The spoiler filter (docs/plan.md, section 6): hides features first seen after the reader's progress, cuts
// each journey at the last stop reached, and, while spoiler mode is on, keeps only the spoiler-safe note.

// Context towns are never named in the book; the schema shows them at every reading position.
export function shownAt(props: GeoJsonProperties, reached: string): boolean {
  return props?.role === 'context' || (typeof props?.first_seen === 'string' && props.first_seen <= reached)
}

const EPISODE_ID = /\b[1-4]-(0[1-9]|1[0-4])\b/g
const REASONING_HIDDEN = 'How this was placed draws on later episodes; it shows once you have read further.'

function safeProps(props: GeoJsonProperties, reached: string, spoilers: boolean): GeoJsonProperties {
  if (!spoilers || !props) return props
  const { note_full: _dropped, ...rest } = props
  // Some reasoning cites the episode that confirms a place, which can be later than the place's first mention.
  const reasoning = typeof rest.reasoning === 'string' ? rest.reasoning : null
  if (reasoning && (reasoning.match(EPISODE_ID) ?? []).some((id) => id > reached)) rest.reasoning = REASONING_HIDDEN
  return rest
}

function upTo<G extends Geometry, P extends GeoJsonProperties>(
  fc: FeatureCollection<G, P>,
  keep: (f: Feature<G, P>) => boolean,
  reached: string,
  spoilers: boolean,
): FeatureCollection<G, P> {
  return {
    ...fc,
    features: fc.features.filter(keep).map((f) => ({ ...f, properties: safeProps(f.properties, reached, spoilers) as P })),
  }
}

export function storyUpTo(story: Story, reached: string, spoilers: boolean): Story {
  const shown = (f: Feature) => shownAt(f.properties, reached)
  const stops = upTo(story.stops, shown, reached, spoilers)
  // A route segment joins stop `sequence` to the next one, so a journey ends at its last stop reached.
  const lastStop = new Map<string, number>()
  for (const f of stops.features) {
    const { journey, sequence } = f.properties
    if (journey && sequence) lastStop.set(journey, Math.max(lastStop.get(journey) ?? 0, sequence))
  }
  const segmentReached = (f: Feature) =>
    shown(f) && (f.properties?.sequence ?? Infinity) < (lastStop.get(f.properties?.journey) ?? 0)
  return {
    places: upTo(story.places, shown, reached, spoilers),
    stops,
    areas: upTo(story.areas, shown, reached, spoilers),
    journeys: upTo(story.journeys, segmentReached, reached, spoilers),
  }
}

// Mountain glyphs come from the base style, not the story sources; a few are named only later in the book.
// The rest carry first_seen 1-01: they are the land itself, named from gazetteers, and like context towns
// they show at every reading position, "not started" included.
export const GLYPH_LAYER = 'mountain-glyph'
export const GLYPH_ALWAYS = '1-01'

export function glyphFilterUpTo(base: FilterSpecification | undefined, reached: string): FilterSpecification {
  const upToHere: ExpressionSpecification = ['<=', ['to-string', ['get', 'first_seen']], reached > GLYPH_ALWAYS ? reached : GLYPH_ALWAYS]
  return base ? ['all', base as ExpressionSpecification, upToHere] : upToHere
}

// A copy of a style with the glyph layer filtered to the reader's progress.
export function styleUpTo(style: StyleSpecification, reached: string): StyleSpecification {
  return {
    ...style,
    layers: style.layers.map((l) => (l.id === GLYPH_LAYER && l.type === 'symbol' ? { ...l, filter: glyphFilterUpTo(l.filter, reached) } : l)),
  }
}
