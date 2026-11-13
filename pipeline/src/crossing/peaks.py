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
So are unnamed summits there that the landform rules clearly call a mesa.

Passes are glyphs too (kind "pass"): named GNIS gaps and GeoNames passes that
lie on a key col, then unnamed key cols of the most prominent summits where the
ground rises on both sides, as a mountain pass rather than a basin divide.

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
import tomllib
from pathlib import Path

import numpy as np
import rasterio
from pyproj import Transformer

from crossing import landforms

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
# Unnamed mesas: low summits (from SHAPE_MIN_PROMINENCE_M) that crossing.landforms calls a mesa from the
# DEM alone, by the margins in [detect] in pipeline/seeds/landforms.toml, and that lie this far from any glyph.
MESA_CLEAR_M = 2000
# Passes. Named ones from GNIS gaps and GeoNames passes, kept only where a key col of a summit with at least
# NAMED_PASS_MIN_COL_M of prominence lies within PASS_SNAP_M, so water gaps and canyon names drop out.
PASS_GNIS_CLASSES = {"Gap"}
PASS_GEONAMES_CODES = {"PASS"}
PASS_SNAP_M = 800
NAMED_PASS_MIN_COL_M = 100
# Unnamed ones: key cols of summits with at least UNNAMED_PASS_MIN_COL_M of prominence. Many of those lie on
# open basin floors, so the ground on a ring PASS_RING_M out must rise PASS_RING_RELIEF_M on two sides and fall
# below the col on the two between. Passes keep PASS_CLEAR_M apart, named ones placed first.
UNNAMED_PASS_MIN_COL_M = 600
PASS_RING_M = 1600
PASS_RING_RELIEF_M = 150
PASS_CLEAR_M = 3000
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


def prominence(dem: np.ndarray) -> list[tuple[int, int, float, float, int]]:
    """(row, col, elevation, prominence, key col cell) for every peak, by a union-find sweep from the top down.

    The key col cell is a flat index into `dem`, or -1 where the key col lies outside the mosaic.
    """
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
            peaks.append((s // cols, s % cols, flat[s], flat[s] - flat[i], int(i)))
            parent[other] = keep
        parent[i] = keep
    for s in summit.values():  # islands that never met higher ground: their key col lies outside the mosaic
        peaks.append((s // cols, s % cols, flat[s], float("inf"), -1))
    return peaks


def gazetteer(to_utm: Transformer, gnis_classes: set[str], geonames_codes: set[str]) -> list[tuple[str, str, str, str, float, float]]:
    """(name, source, source_id, code, x, y) for named features; code is "gnis:<class>" or a GeoNames code."""
    found = []
    for path in GNIS_FILES:
        with path.open(encoding="utf-8-sig", newline="") as f:
            for r in csv.DictReader(f, delimiter="|"):
                if r["feature_class"] in gnis_classes and r["prim_lat_dec"]:
                    x, y = to_utm.transform(float(r["prim_long_dec"]), float(r["prim_lat_dec"]))
                    found.append((r["feature_name"], "gnis", r["feature_id"], f"gnis:{r['feature_class']}", x, y))
    with GEONAMES.open(encoding="utf-8") as f:
        for line in f:
            r = line.split("\t")
            if r[7] in geonames_codes:
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


def is_saddle(dem: np.ndarray, r: int, c: int, relief: float) -> bool:
    """True where the ground PASS_RING_M from cell (r, c) rises `relief` on two sides and falls on two others."""
    k = PASS_RING_M / GRID_M
    a = np.linspace(0, 2 * np.pi, 32, endpoint=False)
    rr, cc = np.rint(r + k * np.sin(a)).astype(int), np.rint(c + k * np.cos(a)).astype(int)
    if rr.min() < 0 or cc.min() < 0 or rr.max() >= dem.shape[0] or cc.max() >= dem.shape[1]:
        return False
    ring = dem[rr, cc]
    if (ring < -9000).any():
        return False
    h = ring - dem[r, c]
    marks = [1 if v >= relief else -1 for v in h if v >= relief or v < 0]
    # Runs of high and low ground around the ring, joined across the start.
    runs = [m for i, m in enumerate(marks) if i == 0 or m != marks[i - 1]]
    if len(runs) > 1 and runs[0] == runs[-1]:
        runs.pop()
    return runs.count(1) >= 2 and runs.count(-1) >= 2


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
    old_kinds = np.array([f["properties"]["kind"] for f in old])
    old_xy = np.array([to_utm.transform(*f["geometry"]["coordinates"]) for f in old])
    claimed: set[int] = set()
    used: set[str] = set()
    fresh = []
    for f in feats:  # biggest first, so they claim first
        x, y = to_utm.transform(*f["geometry"]["coordinates"])
        d = np.hypot(old_xy[:, 0] - x, old_xy[:, 1] - y)
        d[list(claimed)] = np.inf
        d[old_kinds != f["properties"]["kind"]] = np.inf
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

    names = gazetteer(to_utm, GNIS_CLASSES, GEONAMES_CODES)
    names_xy = np.array([(n[4], n[5]) for n in names])
    summit_name = np.array([n[3] in SUMMIT_CODES for n in names])
    feats = []

    def add(x, y, elev, prom, name, src, sid, code=None, kind="peak"):
        lon, lat = to_wgs.transform(x, y)
        pid = f"{kind}-{round(abs(lat) * 1000)}-{round(abs(lon) * 1000)}"  # thousandths of a degree N and W
        props = {
            "id": pid, "name": name or f"Unnamed {'pass' if kind == 'pass' else 'summit'}", "kind": kind, "role": None,
            "part": int(BOOK_SUMMITS.get(name, "1-01")[0]), "first_seen": BOOK_SUMMITS.get(name, "1-01"),
            "certainty": "located", "method": "generated",
            "source": src, "source_id": sid,
            "source_licence": "Copernicus WorldDEM-30 licence" if src == "copernicus-glo30" else ("Public domain" if src == "gnis" else "CC BY 4.0"),
            "note_safe": "", "elevation_m": round(float(elev)),
            # None where the key col lies outside the mosaic, so prominence is unknown. For a pass, the
            # prominence of the summit whose key col it is.
            "prominence_m": None if prom == float("inf") else round(float(prom)),
            # Passes are small marks whatever their col, so they never outrank a summit.
            "size": "small" if kind == "pass" else size_class(prom),
            "name_code": code,
        }
        props |= variation(props["id"])
        feats.append({"type": "Feature", "geometry": {"type": "Point", "coordinates": [round(lon, 5), round(lat, 5)]}, "properties": props})

    for r, c, elev, prom, _ in sorted(big, key=lambda p: -p[3]):
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
    small_xy = np.array([transform * (c + 0.5, r + 0.5) for r, c, *_ in small])
    used = set()  # local summits already given to a named shape
    for name, src, sid, code, x, y in names:
        if name in kept or not (code in SHAPE_CODES or SHAPE_WORDS.search(name)):
            continue
        d = np.hypot(small_xy[:, 0] - x, small_xy[:, 1] - y)
        j = int(d.argmin())
        if d[j] <= SHAPE_RADIUS_M and j not in used:
            r, c, elev, prom, _ = small[j]
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

    # Unnamed mesas and tablelands that the landform rules can see in the DEM.
    cfg = tomllib.loads(landforms.CONFIG.read_text(encoding="utf-8"))
    detect = cfg["detect"]
    glyph_xy = [to_utm.transform(*f["geometry"]["coordinates"]) for f in feats]
    mesas = 0
    with tempfile.TemporaryDirectory() as tmp:
        vrt = Path(tmp) / "dem.vrt"
        subprocess.run(["gdalbuildvrt", "-q", str(vrt), *map(str, sorted(DEM_TILES.glob("*.tif")))], check=True)
        with rasterio.open(vrt) as src:
            for j, (r, c, elev, prom, _) in sorted(enumerate(small), key=lambda p: -p[1][3]):
                x, y = transform * (c + 0.5, r + 0.5)
                if j in used or np.hypot(*(np.array(glyph_xy) - (x, y)).T).min() < MESA_CLEAR_M:
                    continue
                metrics = landforms.measure(src, *to_wgs.transform(x, y), round(float(prom)), cfg["dem"])
                if not metrics:
                    continue
                result = landforms.score({"name": "Unnamed summit"}, metrics, cfg)
                if (result["landform"] in detect["landforms"] and result["margin"] >= detect["min_margin"]
                        and metrics["top_slope"] <= detect["max_top_slope"] and metrics["top_share"] >= detect["min_top_share"]):
                    add(x, y, elev, prom, None, "copernicus-glo30", None)
                    glyph_xy.append((x, y))
                    mesas += 1
    print(f"{mesas} unnamed mesas found from the DEM below {MIN_PROMINENCE_M} m prominence")

    # Passes: the key col of every summit, with the prominence of the summit it separates.
    col_prom: dict[int, float] = {}
    for _, _, _, prom, col in all_peaks:
        if col >= 0:
            col_prom[col] = max(prom, col_prom.get(col, 0))
    col_cells = np.array(list(col_prom))
    col_p = np.array(list(col_prom.values()))
    col_rc = np.column_stack(np.divmod(col_cells, dem.shape[1]))
    col_xy = np.column_stack(transform * (col_rc[:, 1] + 0.5, col_rc[:, 0] + 0.5))
    pass_xy: list[tuple[float, float]] = []

    def clear(x: float, y: float) -> bool:
        return not pass_xy or np.hypot(*(np.array(pass_xy) - (x, y)).T).min() >= PASS_CLEAR_M

    story_names = {f["properties"]["name"] for f in json.loads((REPO / "data" / "places.geojson").read_text(encoding="utf-8"))["features"]}
    named_passes = []
    for name, src, sid, code, x, y in gazetteer(to_utm, PASS_GNIS_CLASSES, PASS_GEONAMES_CODES):
        if name in story_names:  # the story layer already marks and labels it
            continue
        d = np.hypot(col_xy[:, 0] - x, col_xy[:, 1] - y)
        d[col_p < NAMED_PASS_MIN_COL_M] = np.inf
        k = int(d.argmin())
        if d[k] <= PASS_SNAP_M:
            named_passes.append((col_p[k], name, src, sid, code, x, y, dem.flat[col_cells[k]]))
    named_count = 0
    for prom, name, src, sid, code, x, y, elev in sorted(named_passes, key=lambda p: -p[0]):
        if clear(x, y):
            add(x, y, elev, prom, name, src, sid, code, kind="pass")
            pass_xy.append((x, y))
            named_count += 1
    unnamed_count = 0
    for k in np.argsort(-col_p, kind="stable"):
        if col_p[k] < UNNAMED_PASS_MIN_COL_M:
            break
        (r, c), (x, y) = col_rc[k], col_xy[k]
        if clear(x, y) and is_saddle(dem, r, c, PASS_RING_RELIEF_M):
            add(x, y, dem[r, c], col_p[k], None, "copernicus-glo30", None, kind="pass")
            pass_xy.append((x, y))
            unnamed_count += 1
    print(f"passes: {named_count} named (of {len(named_passes)} on a key col), {unnamed_count} unnamed")

    print(f"{keep_ids(feats, to_utm)} ids carried over from the previous {OUT.name}")
    OUT.write_text(json.dumps({"type": "FeatureCollection", "features": feats}, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    named_count = sum(1 for f in feats if not f["properties"]["name"].startswith("Unnamed "))
    print(f"{OUT.name}: {len(feats)} glyphs, {named_count} named; sizes "
          + ", ".join(f"{s} {sum(1 for f in feats if f['properties']['size'] == s)}" for s in ("large", "medium", "small")))


if __name__ == "__main__":
    main()
