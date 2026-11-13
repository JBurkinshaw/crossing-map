// WCAG 2 contrast ratios for the lamplight review (review/stage-6/lamplight). Each colour is composited over
// its background at the given opacity first.
// Usage: node contrast.mjs '[["name", "#fg", "#bg", opacity, needed], ...]'
//        node contrast.mjs mix <colour> <background> <opacity>   (the colour shown)
const hex = (h) => [1, 3, 5].map((i) => parseInt(h.slice(i, i + 2), 16))
const parse = (c) => {
  if (c.startsWith('#')) return [...hex(c), 1]
  const m = c.match(/[\d.]+/g).map(Number)
  return [m[0], m[1], m[2], m[3] ?? 1]
}
const over = (fg, bg) => fg.slice(0, 3).map((v, i) => v * fg[3] + bg[i] * (1 - fg[3]))
const lum = (rgb) => {
  const [r, g, b] = rgb.map((v) => {
    v /= 255
    return v <= 0.03928 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4
  })
  return 0.2126 * r + 0.7152 * g + 0.0722 * b
}
const contrast = (fg, bg, opacity = 1) => {
  const b = parse(bg).slice(0, 3)
  const f = parse(fg)
  f[3] *= opacity
  const [l1, l2] = [lum(over(f, b)), lum(b)].sort((a, c) => c - a)
  return (l1 + 0.05) / (l2 + 0.05)
}
const mix = (a, b, t) => '#' + over([...parse(a).slice(0, 3), t], parse(b)).map((v) => Math.round(v).toString(16).padStart(2, '0')).join('')

if (process.argv[2] === 'mix') console.log(mix(process.argv[3], process.argv[4], Number(process.argv[5])))
else {
  for (const [name, fg, bg, op, need] of JSON.parse(process.argv[2] ?? '[]')) {
    const c = contrast(fg, bg, op ?? 1)
    console.log(`${c >= (need ?? 4.5) ? 'pass' : 'FAIL'} | ${c.toFixed(2)}:1 | ${name} | ${fg}${op && op !== 1 ? ' at ' + op : ''} on ${bg} | ${need ?? 4.5}`)
  }
}
