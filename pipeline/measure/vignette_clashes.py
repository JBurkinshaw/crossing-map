"""How many vignettes cover a stop or a route line on screen, quoted in decision 0026.

Run from the repo root: uv run --project pipeline python pipeline/measure/vignette_clashes.py [VIGNETTES.geojson] [-v]
Without a path it reads data/vignettes.geojson; give an older copy (git show REV:data/vignettes.geojson > /tmp/x)
to compare. -v lists each drawing that clashes.

A drawing clashes if it or its caption covers a stop marker, or more route line than its own width (LINE_OK). Two
drawings overlap if their boxes meet at the zoom where both first show.

Method: each drawing's box and caption box, at its own min_zoom and at zoom 10, laid out as site/src/map/relief.ts
draws them (crossing.build_vignettes.footprint), against the stop markers and route lines of all seven journeys and
the other place pins. Screen pixels are Web Mercator (EPSG:3857) pixels with MapLibre's 512 px tiles. Coordinates
are the published layers' (data/stops.geojson, places.geojson, journeys.geojson, vignettes.geojson; WGS 84),
projected with pyproj. Caption widths are estimates (0.47 em a character); the other sizes are the site's.
"""

import json
import sys
from pathlib import Path

from shapely.geometry import Point

from crossing.build_vignettes import LINE_OK, MERC, Drawing, Story, load
from crossing.paths import DATA


def measure(features: list[dict], story: Story, zoom_of) -> dict:
    """Totals over the drawings shown at the zoom `zoom_of(props)` gives (None: not shown)."""
    rows = []
    for f in features:
        p = f["properties"]
        z = zoom_of(p)
        if z is not None:
            d = Drawing(Point(MERC.transform(*f["geometry"]["coordinates"])), p["side"], z, p["label"])
            rows.append((p["id"], d, story.clash(d)))
    pairs = sum(1 for i, (_, a, _) in enumerate(rows) for _, b, _ in rows[i + 1:] if a.overlaps(b))
    return {
        "shown": len(rows),
        "clashing": [r for r in rows if not r[2].clear],
        "on_stops": sum(1 for r in rows if r[2].stops),
        "on_lines": sum(1 for r in rows if r[2].route_px > LINE_OK * r[2].width_px),
        "stops": sum(r[2].stops for r in rows),
        "route_px": round(sum(r[2].route_px for r in rows)),
        "places": sum(r[2].places for r in rows),
        "drawing_pairs": pairs,
    }


def main() -> None:
    args = [a for a in sys.argv[1:] if a != "-v"]
    path = Path(args[0]) if args else DATA / "vignettes.geojson"
    features = json.loads(path.read_text(encoding="utf-8"))["features"]
    story = Story(*load())
    for name, zoom_of in (("at each drawing's min_zoom", lambda p: p["min_zoom"]),
                          ("at zoom 10", lambda p: 10 if p["min_zoom"] <= 10 else None)):
        m = measure(features, story, zoom_of)
        print(f"{path.name}, {name}: {m['shown']} drawings shown; {len(m['clashing'])} clash "
              f"({m['on_stops']} cover a stop marker, {m['on_lines']} more than their own width of route line); "
              f"{m['stops']} stop markers and {m['route_px']} px of route line covered in all; "
              f"{m['places']} other place pins; {m['drawing_pairs']} pairs of drawings overlap")
        if "-v" in sys.argv:
            for vid, d, c in m["clashing"]:
                print(f"  {vid} at z{d.zoom:g}, {d.side}: {c.stops} stops, {c.route_px} px of line, {c.places} places")


if __name__ == "__main__":
    main()
