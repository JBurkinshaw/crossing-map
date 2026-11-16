// What each kind of route line means, in the reader's words: the layer key and a leg's card both say it so
// (decision 0033). Keyed as tokens.routeLines is: traced (method narrated-path), modeled, curve (schematic).
export const ROUTE_LABEL = {
  traced: 'Follows the road or river the book names',
  modeled: 'Likely route over the terrain, worked out by this site: the book doesn’t trace it',
  curve: 'Route not known: the line only joins the stops',
} as const

// A route segment's label from its method.
export function routeLabel(method: string | undefined): string | null {
  if (method === 'narrated-path') return ROUTE_LABEL.traced
  if (method === 'modeled') return ROUTE_LABEL.modeled
  if (method === 'schematic') return ROUTE_LABEL.curve
  return null
}
