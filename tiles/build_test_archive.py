"""Build tiles/out/test.pmtiles: the story box and a 1-degree graticule.

Stage 0 uses this small archive to prove the host answers PMTiles range
requests. Later stages replace it with the literary basemap.
Run from the repo root: uv run --project pipeline python tiles/build_test_archive.py
"""

import json
import subprocess
import tempfile
from pathlib import Path

OUT = Path(__file__).parent / "out" / "test.pmtiles"
WEST, SOUTH, EAST, NORTH = -113, 27, -104, 36  # the story box, plan section 7


def line(coords, **props):
    return {"type": "Feature", "properties": props, "geometry": {"type": "LineString", "coordinates": coords}}


def main() -> None:
    box = [line([[WEST, SOUTH], [EAST, SOUTH], [EAST, NORTH], [WEST, NORTH], [WEST, SOUTH]], name="story box")]
    grid = [line([[lon, SOUTH], [lon, NORTH]], deg=lon) for lon in range(WEST, EAST + 1)]
    grid += [line([[WEST, lat], [EAST, lat]], deg=lat) for lat in range(SOUTH, NORTH + 1)]

    OUT.parent.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        layers = {}
        for name, features in {"story_box": box, "graticule": grid}.items():
            path = Path(tmp) / f"{name}.geojson"
            path.write_text(json.dumps({"type": "FeatureCollection", "features": features}))
            layers[name] = path
        subprocess.run(
            ["tippecanoe", "-q", "-f", "-o", str(OUT), "-Z4", "-z8"]
            + [arg for name, path in layers.items() for arg in ("-L", f"{name}:{path}")],
            check=True,
        )
    print(f"Wrote {OUT} ({OUT.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
