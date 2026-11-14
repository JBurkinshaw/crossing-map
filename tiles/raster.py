"""Web-tile grids and the MBTiles-to-PMTiles step shared by the two terrain builds."""

import math
import sqlite3
import subprocess
from collections.abc import Iterable, Sequence
from pathlib import Path


def tile_range(z: int, box: Sequence[float]) -> list[tuple[int, int, int]]:
    """The XYZ tiles at zoom z that cover a west, south, east, north box."""
    west, south, east, north = box
    n = 2**z

    def row(lat: float) -> int:
        r = math.radians(lat)
        return int((1 - math.log(math.tan(r) + 1 / math.cos(r)) / math.pi) / 2 * n)

    xs = range(int((west + 180) / 360 * n), int((east + 180) / 360 * n) + 1)
    ys = range(row(north), row(south) + 1)
    return [(z, x, y) for x in xs for y in ys]


def write_pmtiles(out: Path, tiles: Iterable[tuple[int, int, int, bytes]], meta: dict[str, str]) -> None:
    """Write (z, x, y, data) tiles with `meta` to an MBTiles file and convert it to PMTiles at `out` with the
    `pmtiles` CLI."""
    out.parent.mkdir(parents=True, exist_ok=True)
    mbtiles = out.with_suffix(".mbtiles")
    mbtiles.unlink(missing_ok=True)
    db = sqlite3.connect(mbtiles)
    db.executescript("CREATE TABLE metadata (name TEXT, value TEXT);"
                     "CREATE TABLE tiles (zoom_level INTEGER, tile_column INTEGER, tile_row INTEGER, tile_data BLOB);")
    db.executemany("INSERT INTO metadata VALUES (?, ?)", meta.items())
    # MBTiles rows count from the south (TMS); XYZ rows count from the north.
    db.executemany("INSERT INTO tiles VALUES (?, ?, ?, ?)", ((z, x, 2**z - 1 - y, data) for z, x, y, data in tiles))
    db.commit()
    db.close()
    subprocess.run(["pmtiles", "convert", str(mbtiles), str(out)], check=True)
    mbtiles.unlink()
