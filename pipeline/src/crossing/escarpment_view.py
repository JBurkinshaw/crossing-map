"""Experiment: where on the eastern escarpment can Billy see what the book has him see? (J3 stop 5, episode 2-01)

Run from the repo root:
    uv run --project pipeline python -m crossing.escarpment_view
    uv run --project pipeline --with matplotlib python -m crossing.escarpment_view --figure

Writes review/experiments/escarpment-view/ (results.csv, observers.geojson, and img/ with --figure). Reads local
caches only. Nothing here changes the published data. See the folder's README for the findings.

The book (paraphrased): at the eastern escarpment of the Sierras he leads his horse along a rim of grey rock, sits and
looks east over the broad barranca of the Bavispe to the Carretas Plain beyond, with ranges beyond the plain, and sees
a locomotive's smoke on the plain about forty miles away. Then he goes down to the river and rides north along it to a
ford.

The test, for observers along the escarpment west of the upper Bavispe:

1. Ground. The Copernicus GLO-30 DEM (private/cache/least-cost/dem.vrt) warped to a transverse Mercator grid (WGS 84,
   centred at 30.3 N, 108.6 W) at 90 m, averaged.
2. The river. INEGI's 1:50,000 streams (RH09) of Strahler order 7 and up in the box, which is the Bavispe's main stem
   from Mesa Tres Ríos down past Bavispe town.
3. Escarpment. A cell west of the river, within 15 km of it, whose ground drops at least 300 m within 6 km to the east
   (the rule the stop's area already uses, decision 0050). Observers are the cell with the largest drop in each 2 km
   band of northing, between 29.7 N and 30.8 N.
4. What each observer sees, by gdal_viewshed with the eye 1.7 m above the ground and the earth's curvature and
   refraction (coefficient 0.13, the GDAL default):
   - the river below: main-stem cells within 15 km, seen at ground level;
   - the Carretas Plain: flat ground (slope under 2 degrees on a 270 m smoothed grid) joined to GeoNames' point for
     the Llanos de Carretas (4015316, rounded to 31.0 N, 108.5 W). That flat runs on south to Casas Grandes as one
     plain, so "Carretas" is its part within 35 km of the GeoNames point or the old Hacienda Carretas (4015318,
     30.65189 N, 108.79381 W). Both are seen at ground level;
   - the railway: Natural Earth's railways (the line through Casas Grandes and Mata Ortiz is of the period), seen as
     smoke 50 m above the track, and how far away the nearest seen stretch is. Forty miles is 64 km.
"""

import argparse
import csv
import json
import math
import subprocess

import numpy as np
import rasterio
import shapely
from pyproj import CRS, Geod, Transformer
from rasterio.features import rasterize, shapes
from rasterio.transform import from_origin
from rasterio.warp import Resampling, reproject
from scipy import ndimage
from shapely.geometry import shape

from crossing.paths import CACHE, DATA, REPO

DEM = CACHE / "least-cost" / "dem.vrt"
STREAMS = CACHE / "least-cost" / "inegi-streams.geojson"
RAILWAYS = CACHE / "least-cost" / "ne_10m_railroads.geojson"
WORK = CACHE / "escarpment-view"
OUT = REPO / "review" / "experiments" / "escarpment-view"
GEOD = Geod(ellps="WGS84")

CENTRE = (-108.6, 30.3)
BOX = (-109.6, 29.5, -107.4, 31.3)       # lon/lat: the escarpment, the plain and the railway
RES = 90.0
EYE = 1.7
SMOKE = 50.0
DROP_M, DROP_KM = 300, 6
WEST_KM = 15
BAND_KM = 2
LATS = (29.7, 30.8)
RIVER_SEE_KM = 15
FLAT_DEG = 2.0
HACIENDA = (-108.79381, 30.65189)
PLAIN_POINT = (-108.5, 31.0)              # GeoNames 4015316, Llanos de Carretas (rounded to the half degree)
HUISIACHEPIC = (-108.78567, 30.07476)     # the stop's pin, on the Bavispe's main stem
CARRETAS_KM = 35
SAMPLE_KM = 1.5                           # spacing of the escarpment lookouts sampled for the whole-escarpment test
FORTY_MILES_KM = 64.4


def km(a, b) -> float:
    return GEOD.inv(a[0], a[1], b[0], b[1])[2] / 1000


def prepare() -> dict:
    """The DEM on the local grid, written once to the cache for gdal_viewshed."""
    crs = CRS.from_proj4(f"+proj=tmerc +lat_0={CENTRE[1]} +lon_0={CENTRE[0]} +k=1 +x_0=0 +y_0=0 +ellps=WGS84 "
                         "+units=m +no_defs")
    fwd = Transformer.from_crs(4326, crs, always_xy=True)
    xs, ys = fwd.transform([BOX[0], BOX[2], BOX[0], BOX[2]], [BOX[1], BOX[1], BOX[3], BOX[3]])
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
    w, h = int((x1 - x0) // RES), int((y1 - y0) // RES)
    transform = from_origin(x0, y1, RES, RES)
    path = WORK / "dem.tif"
    if not path.exists():
        WORK.mkdir(parents=True, exist_ok=True)
        z = np.full((h, w), np.nan, dtype="float32")
        with rasterio.open(DEM) as src:
            reproject(rasterio.band(src, 1), z, dst_transform=transform, dst_crs=crs, resampling=Resampling.average,
                      src_nodata=src.nodata, dst_nodata=np.nan)
        with rasterio.open(path, "w", driver="GTiff", width=w, height=h, count=1, dtype="float32", crs=crs,
                           transform=transform, nodata=np.nan) as dst:
            dst.write(z, 1)
    with rasterio.open(path) as src:
        z = src.read(1)
    return dict(z=z, transform=transform, crs=crs, fwd=fwd, inv=Transformer.from_crs(crs, 4326, always_xy=True),
                path=path, h=z.shape[0], w=z.shape[1])


def burn(g: dict, geoms: list, all_touched=True) -> np.ndarray:
    local = [shapely.transform(x, lambda xy: np.column_stack(g["fwd"].transform(xy[:, 0], xy[:, 1]))) for x in geoms]
    if not local:
        return np.zeros((g["h"], g["w"]), bool)
    return rasterize([(x, 1) for x in local], out_shape=(g["h"], g["w"]), transform=g["transform"],
                     all_touched=all_touched, dtype="uint8").astype(bool)


def lonlat(g: dict, r: int, c: int) -> tuple[float, float]:
    x, y = g["transform"] * (c + 0.5, r + 0.5)
    lon, lat = g["inv"].transform(x, y)
    return round(lon, 5), round(lat, 5)


def cell(g: dict, lon: float, lat: float) -> tuple[int, int]:
    col, row = ~g["transform"] * g["fwd"].transform(lon, lat)
    return int(row), int(col)


def bavispe() -> list:
    """The Bavispe's main stem: INEGI streams of order 7 and up joined to the stream nearest Huisiachepic's pin,
    which is on the main stem. Other rivers of that order in the box (the Casas Grandes, the Aros) are left out."""
    box = shapely.box(*BOX)
    lines = [shape(f["geometry"]) for f in json.loads(STREAMS.read_text())["features"]
             if f["geometry"] and f["properties"]["ORDER_1"] >= 7 and shape(f["geometry"]).intersects(box)]
    blobs = list(getattr(u := shapely.unary_union([x.buffer(0.01) for x in lines]), "geoms", [u]))
    seed = shapely.Point(HUISIACHEPIC)
    river = min(blobs, key=lambda b: b.distance(seed))
    # INEGI's lines break between some sheets (one break is just north of Bacerac), so join pieces up to 3 km apart.
    while near := [b for b in blobs if 0 < b.distance(river) < 0.03 and not b.within(river)]:
        river = shapely.unary_union([river, *near])
    return [x for x in lines if x.intersects(river)]


def layers(g: dict) -> dict:
    box = shapely.box(*BOX)
    river = burn(g, bavispe())
    rail = burn(g, [shape(f["geometry"]).intersection(box) for f in json.loads(RAILWAYS.read_text())["features"]
                    if shape(f["geometry"]).intersects(box)])
    z = g["z"]
    smooth = ndimage.uniform_filter(np.nan_to_num(z), 3)
    gy, gx = np.gradient(smooth, RES)
    flat = np.degrees(np.arctan(np.hypot(gx, gy))) < FLAT_DEG
    river_col = np.array([np.flatnonzero(row).max() if row.any() else -1 for row in river])
    # The plains east of the sierras: the flat ground joined to GeoNames' point for the Llanos de Carretas. It runs
    # on south to Casas Grandes, so "Carretas" is the part of it within CARRETAS_KM of that point (rounded by
    # GeoNames to the half degree) or of the old hacienda.
    lab, _ = ndimage.label(flat)
    plains = lab == lab[cell(g, *PLAIN_POINT)]
    rr, cc = np.mgrid[0:g["h"], 0:g["w"]]
    near = np.zeros_like(plains)
    for p in (PLAIN_POINT, HACIENDA):
        r, c = cell(g, *p)
        near |= np.hypot(rr - r, cc - c) * RES / 1000 <= CARRETAS_KM
    return dict(river=river, rail=rail, plains=plains, carretas=plains & near, river_col=river_col)


def escarpment_cells(g: dict, lay: dict) -> tuple[np.ndarray, np.ndarray]:
    """Cells west of the river, within WEST_KM of it, whose ground drops DROP_M within DROP_KM to the east, and the
    drop at every cell."""
    z = np.nan_to_num(g["z"], nan=1e4)
    n = int(DROP_KM * 1000 // RES)
    # The lowest ground in the next n cells to the east (columns increase eastward on this grid).
    east_min = ndimage.minimum_filter1d(z, size=n + 1, axis=1, origin=-(n // 2), mode="nearest")
    drop = z - east_min
    cols = np.arange(g["w"])[None, :]
    rc = lay["river_col"][:, None]
    west = (cols < rc) & (cols >= rc - WEST_KM * 1000 / RES) & (rc >= 0)
    return west & (drop >= DROP_M), drop


def sample_views(g: dict, lay: dict, esc: np.ndarray) -> list[dict]:
    """Viewsheds from escarpment cells every SAMPLE_KM (the highest cell in each SAMPLE_KM square), eye 1.7 m
    up: how much of the Carretas Plain each one sees, and how far off."""
    step = int(SAMPLE_KM * 1000 // RES)
    z = np.nan_to_num(g["z"], nan=-1e4)
    rr, cc = np.mgrid[0:g["h"], 0:g["w"]]
    out = []
    for r0 in range(0, g["h"], step):
        for c0 in range(0, g["w"], step):
            sub = esc[r0:r0 + step, c0:c0 + step]
            if not sub.any():
                continue
            zz = np.where(sub, z[r0:r0 + step, c0:c0 + step], -1e4)
            r, c = np.unravel_index(zz.argmax(), zz.shape)
            r, c = r0 + r, c0 + c
            seen = viewshed(g, r, c, 0.0) & lay["carretas"]
            d = np.hypot(rr[seen] - r, cc[seen] - c) * RES / 1000
            out.append({"r": int(r), "c": int(c), "carretas_km2": round(float(seen.sum() * (RES / 1000) ** 2), 1),
                        "nearest_km": round(float(d.min()), 1) if len(d) else None})
    return out


def escarpment(g: dict, lay: dict) -> list[tuple[int, int]]:
    """Observers: per 2 km band of rows, the cell west of the river with the largest drop to the east."""
    ok, drop = escarpment_cells(g, lay)
    out = []
    band = int(BAND_KM * 1000 // RES)
    for r0 in range(0, g["h"], band):
        sub = np.where(ok[r0:r0 + band], drop[r0:r0 + band], -1)
        if sub.max() < 0:
            continue
        r, c = np.unravel_index(sub.argmax(), sub.shape)
        lat = lonlat(g, r0 + r, c)[1]
        if LATS[0] <= lat <= LATS[1]:
            out.append((r0 + r, int(c)))
    return out


def viewshed(g: dict, r: int, c: int, target: float) -> np.ndarray:
    x, y = g["transform"] * (c + 0.5, r + 0.5)
    out = WORK / f"vs-{r}-{c}-{int(target)}.tif"
    if not out.exists():
        subprocess.run(["gdal_viewshed", "-q", "-ox", str(x), "-oy", str(y), "-oz", str(EYE), "-tz", str(target),
                        "-cc", "0.87", "-vv", "1", "-iv", "0", "-ov", "0", "-om", "NORMAL", str(g["path"]), str(out)],
                       check=True, capture_output=True)
    with rasterio.open(out) as src:
        return src.read(1).astype(bool)


def run() -> None:
    g = prepare()
    lay = layers(g)
    obs = escarpment(g, lay)
    cell_km2 = (RES / 1000) ** 2
    rr, cc = np.mgrid[0:g["h"], 0:g["w"]]
    stop = json.loads((DATA / "stops.geojson").read_text(encoding="utf-8"))
    pins = {f["properties"]["id"]: f["geometry"]["coordinates"] for f in stop["features"]}
    rows, feats = [], []
    for r, c in obs:
        here = lonlat(g, r, c)
        ground = viewshed(g, r, c, 0.0)
        smoke = viewshed(g, r, c, SMOKE)
        d_km = np.hypot(rr - r, cc - c) * RES / 1000
        river_seen = (ground & lay["river"] & (d_km <= RIVER_SEE_KM)).sum()
        plain_seen = (ground & lay["carretas"]).sum() * cell_km2
        plains_seen = (ground & lay["plains"]).sum() * cell_km2
        rail_seen = smoke & lay["rail"] & (cc > c)  # east of him: the book has him looking east
        rail_km = float(d_km[rail_seen].min()) if rail_seen.any() else None
        row = {"lon": here[0], "lat": here[1], "height_m": round(float(g["z"][r, c])),
               "drop_m": None, "sees_river": bool(river_seen), "carretas_km2": round(plain_seen, 1),
               "carretas_nearest_km": round(float(d_km[ground & lay["carretas"]].min()), 1) if plain_seen else None,
               "plains_km2": round(plains_seen, 1),
               "plains_nearest_km": round(float(d_km[ground & lay["plains"]].min()), 1) if plains_seen else None,
               "railway_nearest_km": round(rail_km, 1) if rail_km else None,
               "km_from_stop": round(km(here, pins["j3-eastern-escarpment"]), 1),
               "km_from_huisiachepic": round(km(here, pins["j3-huisiachepic"]), 1)}
        rows.append(row)
        feats.append({"type": "Feature", "geometry": {"type": "Point", "coordinates": list(here)},
                      "properties": row})
        print(f"{here[1]:.4f} {here[0]:.4f} {row['height_m']:5} m  river {'yes' if river_seen else 'no ':3}  "
              f"Carretas {plain_seen:7.1f} km2 (nearest {row['carretas_nearest_km']} km)  "
              f"plains {plains_seen:7.1f} km2  "
              f"railway {row['railway_nearest_km']} km")
    OUT.mkdir(parents=True, exist_ok=True)
    with (OUT / "results.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=[k for k in rows[0] if k != "drop_m"], extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)
    plain_poly = [shapely.geometry.shape(s) for s, v in shapes(
        lay["carretas"].astype("uint8"), mask=lay["carretas"], transform=g["transform"]) if v == 1]
    plain_ll = shapely.transform(shapely.unary_union(plain_poly).simplify(200),
                                 lambda xy: np.column_stack(g["inv"].transform(xy[:, 0], xy[:, 1])))
    feats.append({"type": "Feature", "geometry": shapely.geometry.mapping(plain_ll),
                  "properties": {"kind": "carretas-plain"}})
    (OUT / "observers.geojson").write_text(json.dumps({"type": "FeatureCollection", "features": feats}) + "\n")
    esc, _ = escarpment_cells(g, lay)
    samples = sample_views(g, lay, esc)
    bands = []
    for lo in np.arange(29.7, 30.9, 0.1):
        here = [x for x in samples if lo <= lonlat(g, x["r"], x["c"])[1] < lo + 0.1]
        sees = [x for x in here if x["carretas_km2"] >= 1]
        bands.append({"lat_from": round(lo, 1), "lat_to": round(lo + 0.1, 1), "lookouts": len(here),
                      "see_carretas": len(sees),
                      "best_km2": max((x["carretas_km2"] for x in here), default=0),
                      "nearest_km": min((x["nearest_km"] for x in sees), default=None)})
        print(f"{lo:.1f}-{lo + 0.1:.1f} N: {len(here):3} lookouts, {len(sees):3} see 1 km2 or more of the Carretas "
              f"Plain (best {bands[-1]['best_km2']} km2, nearest {bands[-1]['nearest_km']} km)")
    with (OUT / "bands.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(bands[0]))
        w.writeheader()
        w.writerows(bands)
    for x in samples:
        lon, lat = lonlat(g, x["r"], x["c"])
        feats.append({"type": "Feature", "geometry": {"type": "Point", "coordinates": [lon, lat]},
                      "properties": {"kind": "sample", "carretas_km2": x["carretas_km2"],
                                     "nearest_km": x["nearest_km"]}})
    (OUT / "observers.geojson").write_text(json.dumps({"type": "FeatureCollection", "features": feats}) + "\n")
    print(f"{len(rows)} observers. The plains are {lay['plains'].sum() * cell_km2:.0f} km2, the Carretas part "
          f"{lay['carretas'].sum() * cell_km2:.0f} km2")


def figure() -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    g = prepare()
    lay = layers(g)
    rows = [f["properties"] for f in json.loads((OUT / "observers.geojson").read_text())["features"]
            if f["properties"].get("kind") == "sample"]
    for r, f in zip(rows, [f for f in json.loads((OUT / "observers.geojson").read_text())["features"]
                           if f["properties"].get("kind") == "sample"], strict=True):
        r["lon"], r["lat"] = f["geometry"]["coordinates"]
    stops = {f["properties"]["id"]: f["geometry"]["coordinates"]
             for f in json.loads((DATA / "stops.geojson").read_text(encoding="utf-8"))["features"]}
    areas = {f["properties"]["id"]: shape(f["geometry"])
             for f in json.loads((DATA / "areas.geojson").read_text(encoding="utf-8"))["features"]}
    left, top = g["transform"] * (0, 0)
    right, bottom = g["transform"] * (g["w"], g["h"])
    ext = (left, right, bottom, top)
    z = g["z"]
    gy, gx = np.gradient(np.nan_to_num(z), RES)
    slope, aspect = np.arctan(np.hypot(gx, gy)), np.arctan2(-gx, gy)
    shade = np.clip(np.sin(math.radians(45)) * np.cos(slope)
                    + np.cos(math.radians(45)) * np.sin(slope) * np.cos(math.radians(315) - aspect), 0, 1)
    fig, ax = plt.subplots(figsize=(9, 9), dpi=150)
    ax.imshow(shade, cmap="gray", extent=ext)
    ax.imshow(np.ma.masked_where(~lay["plains"], lay["plains"]), cmap="YlOrBr", alpha=0.2, extent=ext, vmin=0, vmax=2)
    ax.imshow(np.ma.masked_where(~lay["carretas"], lay["carretas"]), cmap="YlOrBr", alpha=0.45, extent=ext, vmin=0,
              vmax=1.2)
    ax.imshow(np.ma.masked_where(~lay["river"], lay["river"]), cmap="Blues", alpha=0.9, extent=ext, vmin=0, vmax=1)
    ax.imshow(np.ma.masked_where(~lay["rail"], lay["rail"]), cmap="Greys", alpha=1, extent=ext, vmin=0, vmax=1)

    def xy(p):
        return g["fwd"].transform(*p)
    for aid in ("area-j3-eastern-escarpment", "area-j3-bavispe-promontory"):
        geom = areas.get(aid)
        if geom is None:
            continue
        for poly in getattr(geom, "geoms", [geom]):
            x, y = zip(*(xy(p) for p in poly.exterior.coords), strict=True)
            ax.plot(x, y, color="#7a3fa0" if "escarp" in aid else "#2b5fb3", lw=1)
    sizes = [max(4, float(r["carretas_km2"]) / 2) for r in rows]
    colours = ["#2f8a3b" if float(r["carretas_km2"]) >= 1 else "#b8322a" for r in rows]
    ax.scatter([xy((float(r["lon"]), float(r["lat"])))[0] for r in rows],
               [xy((float(r["lon"]), float(r["lat"])))[1] for r in rows], s=sizes, c=colours, zorder=5,
               edgecolors="k", linewidths=0.4)
    for sid, label in [("j3-eastern-escarpment", "stop 5"), ("j3-huisiachepic", "Huisiachepic"),
                       ("j3-bavispe-promontory", "promontory (stop 2)")]:
        x, y = xy(stops[sid])
        ax.scatter([x], [y], marker="X", s=90, color="k", zorder=6)
        ax.annotate(label, (x, y), xytext=(5, 5), textcoords="offset points", fontsize=8)
    x, y = xy(HACIENDA)
    ax.scatter([x], [y], marker="s", s=40, color="#d9801e", zorder=6)
    ax.annotate("Hacienda Carretas", (x, y), xytext=(5, -10), textcoords="offset points", fontsize=8)
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_title("Lookouts on the escarpment west of the Bavispe, every 1.5 km: green sees 1 km2 or more of the "
                 "Carretas Plain (size: area seen), red sees less.\nPurple: stop 5's area. Blue: stop 2's area. "
                 "Light shading: the plains. Dark shading: the Carretas part. Black line: railway.", fontsize=8)
    fig.tight_layout()
    (OUT / "img").mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT / "img" / "escarpment-view.png")
    print("img/escarpment-view.png")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--figure", action="store_true", help="draw the figure from the last run's results")
    args = ap.parse_args()
    figure() if args.figure else run()


if __name__ == "__main__":
    main()
