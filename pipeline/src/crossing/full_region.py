"""The full-region hachure run (plan 5.2): fine hachures over the whole story box, timed, to size the next step.

Run from the repo root, after `crossing.fetch_dem --story-box`, with QGIS_ENV set as for crossing.hachures:
    QGIS_ENV=/path/to/qgis uv run --project pipeline python -m crossing.full_region [--jobs 10]

The plan builds fine hachures in the journeys corridor first, then returns to the whole region "and times it".
This runs the fine scale over every 40 km tile the DEM covers, outside the corridor too, into the same per-tile
cache (tiles already done are reused), and writes a report to private/overnight/full-region.md: tiles, run time,
strokes, and the sizes the relief and Raised archives would reach, scaled from the corridor's. It does not change
the production build, which reads only the corridor's tiles.
"""

import argparse
import json
import os
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from crossing import hachures as h

REGION = h.REPO / "private" / "cache" / "dem" / "copernicus-region"
REPORT = h.REPO / "private" / "overnight" / "full-region.md"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--jobs", type=int, default=10)
    a = ap.parse_args()
    qgis_env = Path(os.environ["QGIS_ENV"])
    h.DEM_FOLDERS.append(REGION)
    s = h.SCALES["fine"]
    region = h.coverage().buffer(-60)
    corridor = h.corridor().intersection(region)
    grid = h.tiles(region, s["tile"])
    cached = {n for n, _ in grid if (h.OUT / s["folder"] / f"{n}-{s['output']}.geojson").exists()}
    print(f"{len(grid)} tiles over {region.area / 1e6:,.0f} km2; {len(cached)} already cached", flush=True)
    times: dict[str, float] = {}

    def run(t):
        started = time.monotonic()
        h.run_tile("fine", *t, s, qgis_env)
        if t[0] not in cached:
            times[t[0]] = time.monotonic() - started

    wall = time.monotonic()
    with ThreadPoolExecutor(a.jobs) as pool:
        list(pool.map(run, grid))
    wall = time.monotonic() - wall

    def strokes(names) -> int:
        return sum(len(json.loads((h.OUT / s["folder"] / f"{n}-{s['output']}.geojson").read_text())["features"]) for n in names)

    corridor_names = {n for n, _ in h.tiles(corridor, s["tile"])}
    all_strokes, corridor_strokes = strokes(n for n, _ in grid), strokes(corridor_names)
    scale = all_strokes / max(corridor_strokes, 1)
    sizes = {p.name: p.stat().st_size / 1e6 for p in (h.REPO / "tiles" / "out").glob("*.pmtiles")}
    fine_mb, dense_mb = sizes.get("relief.pmtiles", 0), sizes.get("relief-dense.pmtiles", 0)
    raised_mb = sum(v for k, v in sizes.items() if k.startswith("oblique"))
    REPORT.write_text(f"""# Full-region hachure run (plan 5.2)

- Region: {region.area / 1e6:,.0f} km2 the DEM covers in the story box, {len(grid)} fine tiles of 40 km;
  the corridor is {corridor.area / 1e6:,.0f} km2 ({len(corridor_names)} tiles).
- New tiles run: {len(times)}, in {wall / 3600:.1f} h wall time with {a.jobs} jobs
  (per tile: median {sorted(times.values())[len(times) // 2] if times else 0:.0f} s, longest {max(times.values(), default=0):.0f} s).
- Strokes (today's fine density): {all_strokes:,} over the region against {corridor_strokes:,} in the corridor ({scale:.1f} times).
- Projected archives at the same density, scaled by strokes: relief fine and coarse about {fine_mb * scale:.0f} MB
  (corridor {fine_mb:.0f} MB), zoom-12 dense about {dense_mb * scale:.0f} MB (corridor {dense_mb:.0f} MB),
  Raised about {raised_mb * scale:.0f} MB (corridor {raised_mb:.0f} MB). Each would need splitting to stay under
  100 MB per file, and the total counts against GitHub Pages' 1 GB site limit twice (main and preview).
""", encoding="utf-8")
    print(REPORT.read_text())


if __name__ == "__main__":
    main()
