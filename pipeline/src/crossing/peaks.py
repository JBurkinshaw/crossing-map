"""Find significant peaks and write data/mountain_glyphs.geojson (plan section 5.2, layer 2).

Run from the repo root: uv run --project pipeline python -m crossing.peaks
Then run crossing.landforms, which adds each glyph's landform.

Method. Mosaic the Copernicus GLO-30 tiles at GRID_M in UTM 12N, keeping each
cell's highest 30 m elevation ("max" resampling) so summits survive. Compute
topographic prominence by the standard union-find sweep: visit cells from
highest to lowest; a cell with no visited neighbour starts a new island; where
islands meet, the one with the lower summit ends, with prominence = its
summit - the meeting cell (the key col). Keep peaks with at least
MIN_PROMINENCE_M. Prominence is approximate: a 200 m grid smooths cols, and
an island that reaches the edge of the mosaic may have higher ground outside it.

Names come from GNIS (US) and GeoNames (Mexico) summits, hills, mesas, ridges
and volcanoes within NAME_RADIUS_M of a peak; each keeps its feature code
(`name_code`) for crossing.landforms. Every named summit in the book's seeds is
kept even when its prominence is lower. Named mesas, buttes and volcanic cones
are kept from SHAPE_MIN_PROMINENCE_M, since few of them reach MIN_PROMINENCE_M.

Each glyph gets a stable variation seeded by the peak's id: which of the
GLYPHS shapes, a horizontal flip, a scale jitter of +/-15% and a rotation of
+/-3 degrees. Size class follows prominence.
"""

import csv
import hashlib
import json
import re
import subprocess
import tempfile
from pathlib import Path

import numpy as np
import rasterio
from pyproj import Transformer

REPO = Path(__file__).resolve().parents[3]
DEM_TILES = REPO / "private" / "cache" / "dem" / "copernicus"
GNIS_FILES = [REPO / f"private/cache/gazetteer/DomesticNames_{s}_Text/Text/DomesticNames_{s}.txt" for s in ("NM", "AZ")]
GEONAMES = REPO / "private" / "cache" / "gazetteer" / "MX" / "MX.txt"
OUT = REPO / "data" / "mountain_glyphs.geojson"
CRS = "EPSG:32612"
GRID_M = 200
# Not below about 150 m: the 200 m grid smooths cols, so lower prominences are mostly noise.
MIN_PROMINENCE_M = 200
NAME_RADIUS_M = 2000
GNIS_CLASSES = {"Summit", "Ridge", "Bench", "Crater"}
GEONAMES_CODES = {"MT", "PK", "HLL", "HLLS", "MESA", "RDGE", "VLC"}
SUMMIT_CODES = {"gnis:Summit", "MT", "PK"}
# Named shapes the prominence cut would lose, kept down to SHAPE_MIN_PROMINENCE_M at the nearest
# local summit within SHAPE_RADIUS_M.
SHAPE_CODES = {"gnis:Bench", "gnis:Crater", "MESA", "VLC"}
SHAPE_WORDS = re.compile(r"\b(mesa|mesas|mesita|butte|buttes|crater|cráter|volcán|volcan)\b", re.IGNORECASE)
SHAPE_MIN_PROMINENCE_M = 100
SHAPE_RADIUS_M = 1000
# A summit within this distance of a glyph in the previous file keeps that glyph's id, and so its shape.
KEEP_ID_M = 500
GLYPHS = 12
# Summits the book names, with the episode that first names them (from crossing.extract; the book says
# "the Animas Peaks"). Always kept, at their GNIS position. Other summits are plain geography, shown from 1-01.
BOOK_SUMMITS = {"Animas Peak": "2-05", "Gillespie Mountain": "4-01", "Black Point": "1-03"}


def mosaic() -> tuple[np.ndarray, rasterio.Affine]:
    with tempfile.TemporaryDirectory() as tmp:
        vrt, out = Path(tmp) / "m.vrt", Path(tmp) / "m.tif"
        subprocess.run(["gdalbuildvrt", "-q", str(vrt), *map(str, sorted(DEM_TILES.glob("*.tif")))], check=True)
        # -tap pins the grid to multiples of GRID_M, so adding DEM tiles does not move every summit.
        subprocess.run(["gdalwarp", "-q", "-t_srs", CRS, "-tr", str(GRID_M), str(GRID_M), "-tap", "-r", "max",
                        "-dstnodata", "-9999", str(vrt), str(out)], check=True)
        with rasterio.open(out) as src:
            return src.read(1).astype(np.float64), src.transform


def prominence(dem: np.ndarray) -> list[tuple[int, int, float, float]]:
    """(row, col, elevation, prominence) for every peak, by a union-find sweep from the top down."""
    rows, cols = dem.shape
    flat = dem.ravel()
    valid = flat > -9000
    order = np.argsort(-flat, kind="stable")
    order = order[valid[order]]
    parent = np.full(flat.size, -1, dtype=np.int64)  # -1: not yet visited
    summit = {}  # island root -> summit cell

    def find(i: int) -> int:
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    peaks = []
    for i in order:
        r, c = divmod(int(i), cols)
        roots = set()
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                rr, cc = r + dr, c + dc
                if (dr or dc) and 0 <= rr < rows and 0 <= cc < cols and parent[rr * cols + cc] != -1:
                    roots.add(find(rr * cols + cc))
        if not roots:
            parent[i] = i
            summit[i] = i
            continue
        # Join the island with the highest summit; every other island ends here, at its key col.
        roots = sorted(roots, key=lambda k: flat[summit[k]], reverse=True)
        keep = roots[0]
        for other in roots[1:]:
            s = summit.pop(other)
            peaks.append((s // cols, s % cols, flat[s], flat[s] - flat[i]))
            parent[other] = keep
        parent[i] = keep
    for s in summit.values():  # islands that never met higher ground: their key col lies outside the mosaic
        peaks.append((s // cols, s % cols, flat[s], float("inf")))
    return peaks


def named_summits(to_utm: Transformer) -> list[tuple[str, str, str, str, float, float]]:
    """(name, source, source_id, code, x, y) for named relief features; code is "gnis:<class>" or a GeoNames code."""
    found = []
    for path in GNIS_FILES:
        with path.open(encoding="utf-8-sig", newline="") as f:
            for r in csv.DictReader(f, delimiter="|"):
                if r["feature_class"] in GNIS_CLASSES and r["prim_lat_dec"]:
                    x, y = to_utm.transform(float(r["prim_long_dec"]), float(r["prim_lat_dec"]))
                    found.append((r["feature_name"], "gnis", r["feature_id"], f"gnis:{r['feature_class']}", x, y))
    with GEONAMES.open(encoding="utf-8") as f:
        for line in f:
            r = line.split("\t")
            if r[7] in GEONAMES_CODES:
                x, y = to_utm.transform(float(r[5]), float(r[4]))
                found.append((r[1], "geonames", r[0], r[7], x, y))
    return found


def variation(peak_id: str) -> dict:
    h = hashlib.sha256(peak_id.encode()).digest()
    return {
        "glyph": h[0] % GLYPHS + 1,
        "flip": bool(h[1] % 2),
        "glyph_scale": round(0.85 + 0.30 * h[2] / 255, 2),
        "glyph_rotate": round(-3 + 6 * h[3] / 255, 1),
    }


def size_class(prom: float) -> str:
    return "large" if prom >= 1000 else "medium" if prom >= 600 else "small"


def keep_ids(feats: list[dict], to_utm: Transformer) -> int:
    """Give each new glyph the id of the nearest unclaimed glyph in the previous file within KEEP_ID_M.

    Ids come from coordinates, which move a little whenever the mosaic grid
    changes; carrying the old id keeps each glyph's shape, flip and size jitter.
    Returns how many ids carried over.
    """
    if not OUT.exists():
        return 0
    old = json.loads(OUT.read_text(encoding="utf-8"))["features"]
    old_ids = [f["properties"]["id"] for f in old]
    old_xy = np.array([to_utm.transform(*f["geometry"]["coordinates"]) for f in old])
    claimed: set[int] = set()
    used: set[str] = set()
    fresh = []
    for f in feats:  # biggest first, so they claim first
        x, y = to_utm.transform(*f["geometry"]["coordinates"])
        d = np.hypot(old_xy[:, 0] - x, old_xy[:, 1] - y)
        d[list(claimed)] = np.inf
        j = int(d.argmin())
        if d[j] <= KEEP_ID_M:
            claimed.add(j)
            f["properties"] |= {"id": old_ids[j], **variation(old_ids[j])}
            used.add(old_ids[j])
        else:
            fresh.append(f)
    # A new glyph whose own id is already taken takes a suffix.
    for f in fresh:
        pid = base = f["properties"]["id"]
        n = 2
        while pid in used:
            pid, n = f"{base}-{n}", n + 1
        used.add(pid)
        f["properties"] |= {"id": pid, **variation(pid)}
    return len(claimed)


def main() -> None:
    dem, transform = mosaic()
    print(f"mosaic {dem.shape[1]} x {dem.shape[0]} cells at {GRID_M} m")
    to_utm = Transformer.from_crs("EPSG:4326", CRS, always_xy=True)
    to_wgs = Transformer.from_crs(CRS, "EPSG:4326", always_xy=True)
    all_peaks = prominence(dem)
    big = [p for p in all_peaks if p[3] >= MIN_PROMINENCE_M]
    print(f"{len(all_peaks)} local summits; {len(big)} with prominence >= {MIN_PROMINENCE_M} m")

    names = named_summits(to_utm)
    names_xy = np.array([(n[4], n[5]) for n in names])
    summit_name = np.array([n[3] in SUMMIT_CODES for n in names])
    feats = []

    def add(x, y, elev, prom, name, src, sid, code=None):
        lon, lat = to_wgs.transform(x, y)
        pid = f"peak-{round(abs(lat) * 1000)}-{round(abs(lon) * 1000)}"  # thousandths of a degree N and W
        props = {
            "id": pid, "name": name or "Unnamed summit", "kind": "peak", "role": None,
            "part": int(BOOK_SUMMITS.get(name, "1-01")[0]), "first_seen": BOOK_SUMMITS.get(name, "1-01"),
            "certainty": "located", "method": "generated",
            "source": src, "source_id": sid,
            "source_licence": "Copernicus WorldDEM-30 licence" if src == "copernicus-glo30" else ("Public domain" if src == "gnis" else "CC BY 4.0"),
            "note_safe": "", "elevation_m": round(float(elev)),
            # None where the key col lies outside the mosaic, so prominence is unknown.
            "prominence_m": None if prom == float("inf") else round(float(prom)),
            "size": size_class(prom),
            "name_code": code,
        }
        props |= variation(props["id"])
        feats.append({"type": "Feature", "geometry": {"type": "Point", "coordinates": [round(lon, 5), round(lat, 5)]}, "properties": props})

    for r, c, elev, prom in sorted(big, key=lambda p: -p[3]):
        x, y = transform * (c + 0.5, r + 0.5)
        d = np.hypot(names_xy[:, 0] - x, names_xy[:, 1] - y)
        # Out of range first, so a summit name just beyond NAME_RADIUS_M cannot beat a mesa name in range.
        d[d > NAME_RADIUS_M] = np.inf
        # A summit or mountain name in range beats a nearer hill, mesa or ridge name.
        j = int(np.where(summit_name, d, d + NAME_RADIUS_M).argmin())
        named = names[j] if np.isfinite(d[j]) else None
        add(x, y, elev, prom, named[0] if named else None, "copernicus-glo30", named[2] if named else None,
            named[3] if named else None)
    kept = {f["properties"]["name"] for f in feats}
    small = [p for p in all_peaks if SHAPE_MIN_PROMINENCE_M <= p[3] < MIN_PROMINENCE_M]
    small_xy = np.array([transform * (c + 0.5, r + 0.5) for r, c, _, _ in small])
    used = set()  # local summits already given to a named shape
    for name, src, sid, code, x, y in names:
        if name in kept or not (code in SHAPE_CODES or SHAPE_WORDS.search(name)):
            continue
        d = np.hypot(small_xy[:, 0] - x, small_xy[:, 1] - y)
        j = int(d.argmin())
        if d[j] <= SHAPE_RADIUS_M and j not in used:
            r, c, elev, prom = small[j]
            add(*(transform * (c + 0.5, r + 0.5)), elev, prom, name, "copernicus-glo30", sid, code)
            kept.add(name)
            used.add(j)
    print(f"{len(used)} named mesas, buttes and cones added below {MIN_PROMINENCE_M} m prominence")
    for name, src, sid, code, x, y in names:
        if name in BOOK_SUMMITS and name not in kept:
            c, r = ~transform * (x, y)
            elev = dem[int(r), int(c)] if 0 <= int(r) < dem.shape[0] and 0 <= int(c) < dem.shape[1] else 0
            add(x, y, elev, 0, name, src, sid, code)
            kept.add(name)

    print(f"{keep_ids(feats, to_utm)} ids carried over from the previous {OUT.name}")
    OUT.write_text(json.dumps({"type": "FeatureCollection", "features": feats}, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    named_count = sum(1 for f in feats if f["properties"]["name"] != "Unnamed summit")
    print(f"{OUT.name}: {len(feats)} peaks, {named_count} named; sizes "
          + ", ".join(f"{s} {sum(1 for f in feats if f['properties']['size'] == s)}" for s in ("large", "medium", "small")))


if __name__ == "__main__":
    main()
