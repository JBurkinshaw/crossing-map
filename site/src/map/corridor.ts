import type { Geometry, MultiPolygon, Position } from 'geojson'

// Talk on the road (docs/plan.md, section 8): a line spoken while travelling a route segment is shown as that
// segment buffered 2 km, a corridor rather than a point.
export const CORRIDOR_M = 2000

const ARC_STEPS = 12 // points on each half circle at the ends and on each round join

// The outline of a line buffered by `metres`: offset curves on both sides, round on the outside of each bend
// and at both ends, and mitred on the inside. Worked in metres on a local equirectangular plane, which over a
// route segment of a few tens of kilometres is far more exact than the buffer itself. The schematic segments
// are gentle curves; a bend sharper than the buffer can leave a small loop on its inside, which the fill covers.
export function corridor(geometry: Geometry, metres = CORRIDOR_M): MultiPolygon | null {
  const parts = geometry.type === 'LineString' ? [geometry.coordinates] : geometry.type === 'MultiLineString' ? geometry.coordinates : []
  const rings = parts.filter((p) => p.length >= 2).map((p) => [bufferRing(p, metres)])
  return rings.length > 0 ? { type: 'MultiPolygon', coordinates: rings } : null
}

function bufferRing(line: Position[], r: number): Position[] {
  const lat0 = line.reduce((s, p) => s + p[1], 0) / line.length
  const kx = 111320 * Math.cos((lat0 * Math.PI) / 180)
  const ky = 110574
  const lon0 = line[0][0]
  // A path snapped to a road or river zigzags at a scale far below the buffer; simplified first (to a tenth
  // of the buffer), its offset curves stay clear of small loops. Repeated points have no direction.
  const pts = simplify(line.map(([lon, lat]) => [(lon - lon0) * kx, (lat - lat0) * ky]), r / 10)
    .filter((p, i, all) => i === 0 || p[0] !== all[i - 1][0] || p[1] !== all[i - 1][1])
  const back = (p: number[]): Position => [Math.round((p[0] / kx + lon0) * 1e5) / 1e5, Math.round((p[1] / ky + lat0) * 1e5) / 1e5]
  if (pts.length < 2) return circle(pts[0], r).map(back)

  // Unit left normal of each piece of the line.
  const normals = pts.slice(1).map((p, i) => {
    const dx = p[0] - pts[i][0]
    const dy = p[1] - pts[i][1]
    const len = Math.hypot(dx, dy)
    return [-dy / len, dx / len]
  })

  // The left side of a path, walked from its start to its end.
  const side = (path: number[][], ns: number[][]) => {
    const out: number[][] = [offset(path[0], ns[0], r)]
    for (let i = 1; i < path.length - 1; i++) {
      const [a, b] = [ns[i - 1], ns[i]]
      if (a[0] * b[1] - a[1] * b[0] > 0) {
        // The path bends left, so this is the inside of the bend: where the two offset lines meet.
        // A bend sharper than a right angle would put that point far out, so it keeps both offset ends and
        // leaves a small loop inside the corridor instead.
        const mx = a[0] + b[0]
        const my = a[1] + b[1]
        const cos = mx * a[0] + my * a[1] // 1 + the cosine of the bend
        if (cos >= 1) out.push([path[i][0] + (mx * r) / cos, path[i][1] + (my * r) / cos])
        else out.push(offset(path[i], a, r), offset(path[i], b, r))
      } else {
        out.push(...arc(path[i], a, b, r))
      }
    }
    out.push(offset(path[path.length - 1], ns[ns.length - 1], r))
    return out
  }

  const left = side(pts, normals)
  // The right side, walked from the end back to the start, is the left side of the reversed line.
  const rev = [...pts].reverse()
  const right = side(rev, [...normals].reverse().map(([x, y]) => [-x, -y]))
  const end = normals[normals.length - 1]
  const start = normals[0]
  const ring = [
    ...left,
    ...cap(pts[pts.length - 1], end, r),
    ...right,
    ...cap(pts[0], [-start[0], -start[1]], r),
  ]
  ring.push(ring[0])
  return ring.map(back)
}

// Douglas-Peucker: the fewest points that keep the path within `tolerance` of the original.
function simplify(pts: number[][], tolerance: number): number[][] {
  if (pts.length < 3) return pts
  const keep = new Array<boolean>(pts.length).fill(false)
  keep[0] = keep[pts.length - 1] = true
  const stack: [number, number][] = [[0, pts.length - 1]]
  while (stack.length > 0) {
    const [i, j] = stack.pop()!
    const [a, b] = [pts[i], pts[j]]
    const len = Math.hypot(b[0] - a[0], b[1] - a[1])
    let far = -1
    let farD = tolerance
    for (let k = i + 1; k < j; k++) {
      const p = pts[k]
      const d = len === 0 ? Math.hypot(p[0] - a[0], p[1] - a[1]) : Math.abs((b[0] - a[0]) * (a[1] - p[1]) - (a[0] - p[0]) * (b[1] - a[1])) / len
      if (d > farD) {
        far = k
        farD = d
      }
    }
    if (far >= 0) {
      keep[far] = true
      stack.push([i, far], [far, j])
    }
  }
  return pts.filter((_, k) => keep[k])
}

const offset = (p: number[], n: number[], d: number) => [p[0] + n[0] * d, p[1] + n[1] * d]

// The round join on the outside of a bend, from normal a to normal b.
function arc(p: number[], a: number[], b: number[], d: number): number[][] {
  const from = Math.atan2(a[1], a[0])
  let sweep = Math.atan2(b[1], b[0]) - from
  while (sweep > Math.PI) sweep -= 2 * Math.PI
  while (sweep < -Math.PI) sweep += 2 * Math.PI
  const steps = Math.max(1, Math.ceil((Math.abs(sweep) / Math.PI) * ARC_STEPS))
  return Array.from({ length: steps + 1 }, (_, i) => {
    const t = from + (sweep * i) / steps
    return [p[0] + Math.cos(t) * d, p[1] + Math.sin(t) * d]
  })
}

// The half circle round an end of the line, from the left normal n clockwise to its opposite.
function cap(p: number[], n: number[], r: number): number[][] {
  const from = Math.atan2(n[1], n[0])
  return Array.from({ length: ARC_STEPS - 1 }, (_, i) => {
    const t = from - (Math.PI * (i + 1)) / ARC_STEPS
    return [p[0] + Math.cos(t) * r, p[1] + Math.sin(t) * r]
  })
}

function circle(p: number[], r: number): number[][] {
  const ring = Array.from({ length: ARC_STEPS * 2 }, (_, i) => {
    const t = (Math.PI * i) / ARC_STEPS
    return [p[0] + Math.cos(t) * r, p[1] + Math.sin(t) * r]
  })
  ring.push(ring[0])
  return ring
}

// A point near the middle of a line, along its length, for the corridor's label.
export function midpoint(geometry: Geometry): Position | null {
  const line = geometry.type === 'LineString' ? geometry.coordinates : geometry.type === 'MultiLineString' ? geometry.coordinates.flat() : []
  if (line.length === 0) return null
  const lengths = line.slice(1).map((p, i) => Math.hypot(p[0] - line[i][0], p[1] - line[i][1]))
  let half = lengths.reduce((s, l) => s + l, 0) / 2
  for (let i = 0; i < lengths.length; i++) {
    if (half <= lengths[i] && lengths[i] > 0) {
      const t = half / lengths[i]
      return [line[i][0] + (line[i + 1][0] - line[i][0]) * t, line[i][1] + (line[i + 1][1] - line[i][1]) * t]
    }
    half -= lengths[i]
  }
  return line[line.length - 1]
}
