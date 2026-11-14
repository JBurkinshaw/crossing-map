# Hand-drawn mountain glyphs: test sheets (experiment, 13 November 2026)

**Adopted on 14 November 2026: variant B.** Its style now lives in `art/pen.py` (shared with the vignettes) and `art/glyphs/make_glyphs.py`, which rebuilt the 168 SVGs and the sprite byte-for-byte as variant B here. `make_glyphs_hand.py` is deleted; the trial's images, SVGs and sprites are in `private/parked/glyphs-experiment/`.

Nothing here is rolled out. The live glyphs (`art/glyphs/svg/`, `site/public/sprites/`) and `art/glyphs/make_glyphs.py` are unchanged.

## What I tried

A new generator, `art/glyphs/make_glyphs_hand.py`, redraws the current 7 families (peak, dome, mesa, butte, cone, ridge, pass; 12 shapes each plus the mirrored "-flip" twins, 168 glyphs) as pen strokes. It imports the silhouettes and seeds from `make_glyphs.py`, so every glyph keeps its shape, name and canvas size; only the line work changes. Each stroke is a filled outline (not an SVG stroke), so it can have pen pressure:

- **Wobble:** the centre line drifts sideways by smooth noise (three sines, wavelengths of about 7 to 28 units, seeded per shape); the ends move least.
- **Pressure:** full width in the middle, tapering at both ends, with a slow swell along the stroke.
- **Pen lifts:** in B and C the outline is two or three strokes that meet at the summit (the rim of a mesa or butte, a saddle of a ridge, the col of a pass), with a small overshoot or a small gap.
- **Hatching:** spacing, angle and length jitter; some strokes broken in two (B); some rows left out; each hatch tapers.
- **Double stroke:** a thin second pass along part of the shaded flank (B, on about 60% of glyphs).
- Light stays in the north-west on the mirrored twins (hatching redrawn on the right), as now. Only the two inks (#2b2118 on #e4ddcc) are used.

Run: `uv run --project pipeline python art/glyphs/make_glyphs_hand.py [A B C]`. It writes `svg/<V>/` and `sprites/<V>/` here (glyphs plus the 13 vignettes, as the live sprite).

## The three variants

| | Wobble | Outline | Taper (end width) | Pen lifts | Hatching |
|---|---|---|---|---|---|
| **A** light | 0.35 units | 1.5 | to 55% | no | as now, slightly irregular |
| **B** pen and ink | 0.6 | 1.9 | to 20% | yes | looser, 18% broken, double stroke on shaded flank |
| **C** sparse (Blood Meridian-like) | 0.5 | 2.0 | to 25% | yes | a few short strokes under the summit only (top half of the flank), spur drawn 60% of its length |

## Images

- `detail-current.png`, `detail-A.png`, `detail-B.png`, `detail-C.png`: every shape and its mirror at 1.5 times the 1x sprite size.
- `compare-1x.png`, `compare-2x.png`: current, A, B, C side by side, drawn from each sprite bitmap at the icon-size the map uses (0.4 small at zoom 8, 0.5 small, 0.65 medium, 0.85 large), at device pixel ratio 1 and 2. This is the "real size" view.
- `maps/<view>-z<zoom>.jpg`: the real site (dev server on port 5184, a scratch copy of `site/` with its own sprite folder), 2 x 2 (current, A / B, C), device pixel ratio 2, for four views: `peloncillos`, `animas`, `babicora` (Sierra Madre west of the Babícora plain), `bavispe` (the densest glyph cluster, east of the Bavispe). Zoom 8, 10 and 12; `-z10-1x` is the same at ratio 1. At zoom 12 each view is moved onto the nearest glyph cluster, since a crop there holds only one or two glyphs.

## Results

Sprite sizes (bytes; 168 glyphs plus 13 vignettes):

| Set | glyphs.png | glyphs@2x.png | JSON (1x / 2x) | SVG sources |
|---|---|---|---|---|
| current | 141,734 | 251,947 | 19,212 / 19,560 | 246 kB |
| A | 117,247 | 262,280 | same | 1.58 MB |
| B | 121,384 | 274,793 | same | 2.28 MB |
| C | 102,313 | 224,157 | same | 1.76 MB |

The sprite stays the same size or smaller. The SVG sources are 6 to 9 times larger (each stroke is a polygon with a point every 0.7 units); only the sprite ships, so this costs repository size, not download size.

Mean ink per glyph (dark-pixel equivalent, 1x sprite): current 172, A 152 (11% lighter), B 168, C 155. Tapered ends with no round caps take away ink; A would need an outline of about 1.65 to match the current weight.

Readability at the map's sizes:

- **The hand-drawn character shows only on medium and large glyphs, or at ratio 2.** Small glyphs (925 of the 1,004) show at icon-size 0.4 to 0.5, so 1 glyph unit is 0.4 to 0.5 screen pixels at ratio 1. The wobble (0.35 to 0.6 units) is then 0.15 to 0.3 px, which nobody sees; the taper and the heavier middle of the stroke are what survive. At zoom 8 (large glyphs, Chiricahua Peak, the Hatchets in `peloncillos-z8.jpg`) the difference is clear.
- **Tapered feet fade out** at 0.4 and 0.5: B and C glyphs look a little narrower than they are, and the foot no longer meets the ground as firmly.
- **C loses the light side on small peaks and cones.** With hatching only in the top half, a small peak reads as a bare chevron at 0.4, and the cone's crater notch is lost. The north-west light, which plan 5.2 asks for, is weakest in C.
- **B's gaps and broken hatches** are invisible at small sizes (under 0.3 px) and read as pen work only on large glyphs; they do not make glyphs look broken.
- **Not specific to the variants:** at zoom 12 every set looks small against the dense hachures (icon-size stops growing at zoom 10), and the paper fill (#e4ddcc) shows as a faint patch on the lighter paper above zoom 10. Both are true of the current set.

Tracing: `potrace` and `inkscape` are installed (`vtracer` is not). I did not use them: the glyphs are generated as vectors, so there is nothing to trace, and none of the references may be traced (the Blood Meridian map is look-only). They would only help if the owner draws the 12 shapes by hand on paper and scans them; then `potrace` would turn the scans into SVG filled outlines that this pipeline could take in place of the generated silhouettes.

## Recommendation

**B**, possibly with the outline brought back to about 1.7 and the double stroke kept to large glyphs. It is the only variant whose pen work is visible at zoom 8 and on medium glyphs while keeping the full hatching that carries the north-west light at small sizes; its ink weight is closest to the current set (2% lighter). A is a safe, nearly invisible change (lighter than now at small sizes). C is the most striking on large glyphs and the closest to the Blood Meridian look, but at small sizes it drops the shaded flank, which the plan treats as the point of the glyphs. A middle option is B for small glyphs and C-style sparse hatching for large ones, but that needs a second sprite name per size class and a change to `relief.ts`.

## Open questions for the owner

1. Which variant, if any (the `compare-2x.png` and `peloncillos-z8.jpg` sheets show the difference best)?
2. Should the hand treatment be stronger (larger wobble) so it shows on small glyphs too, at the cost of a less tidy look when large?
3. Do you still want truly hand-drawn shapes (plan 5.2: "draw about 12 shapes by hand")? If so, a scan plus `potrace` would replace the generated silhouettes, and this script's pen treatment would no longer be needed.

## What rolling out would change

1. `art/glyphs/make_glyphs.py`: replace its `svg()` drawing with the chosen style from `make_glyphs_hand.py` (move `Style`, the geometry helpers, the hatch functions and `glyph()` in; keep the silhouettes, seeds, names and canvas sizes), or make `make_glyphs_hand.py` write to `art/glyphs/svg/` and call `build_sprite()`. Then delete `make_glyphs_hand.py`.
2. Run `uv run --project pipeline python art/glyphs/make_glyphs.py`. This rewrites the 168 files in `art/glyphs/svg/` and `site/public/sprites/glyphs{,@2x}.{png,json}`. The icon names and sizes do not change, so `site/src/map/relief.ts`, the layer key and `data/mountain_glyphs.geojson` need no change.
3. Optional: re-run `tools/landform-sheet.mjs` for the stage 3 review sheet; note the change in `docs/CHANGELOG.md`, and in plan 5.2 (the families are still generated, now with a pen treatment).

## Files

- `art/glyphs/make_glyphs_hand.py` (new): the generator.
- `tools/glyph-hand-sheet.mjs` (new): the detail and comparison sheets. `cd tools && node glyph-hand-sheet.mjs`.
- `tools/glyph-hand-maps.mjs` and `tools/glyph-hand-maps.py` (new): the map previews. Serve the scratch copy (`cd private/overnight/glyphs/site-copy && npx vite --port 5184`), then `cd tools && node glyph-hand-maps.mjs`, then `uv run --project pipeline python tools/glyph-hand-maps.py`.
- `private/overnight/glyphs/site-copy/`: the scratch site (links to `site/src`, `site/node_modules` and the public data, fonts and tiles; its own `public/sprites`, left holding the current sprite). Safe to delete.
