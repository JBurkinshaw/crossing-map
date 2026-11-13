"""Classify each mountain glyph's landform: peak, dome, mesa, butte, cone or ridge.

Run from the repo root, after crossing.peaks:
    uv run --project pipeline python -m crossing.landforms

Every weight and threshold lives in pipeline/seeds/landforms.toml, which also
explains each measurement. This module only applies them: each summit starts
with the prior, gains points from words in its name, from its gazetteer feature
code and from DEM rules, and takes the landform with the most points. Passes
are not summits: they keep the landform "pass" and are left out of the report.

Writes `landform` and `landform_source` (name, dem or default: the evidence
that gave the winner the most points) into data/mountain_glyphs.geojson, and
every measurement, rule and score to review/stage-3/landforms.csv.
"""

import csv
import json
import re
import subprocess
import tempfile
import tomllib
import unicodedata
from pathlib import Path

import numpy as np
import rasterio
from pyproj import Geod
from rasterio.windows import from_bounds
from scipy import ndimage

REPO = Path(__file__).resolve().parents[3]
CONFIG = REPO / "pipeline" / "seeds" / "landforms.toml"
GLYPHS = REPO / "data" / "mountain_glyphs.geojson"
DEM_TILES = REPO / "private" / "cache" / "dem" / "copernicus"
REPORT = REPO / "review" / "stage-3" / "landforms.csv"
SUMMIT_SEARCH_M = 300  # peaks sit on a 200 m grid; look this far for the 30 m summit
METRICS = ["relief_m", "top_share", "top_slope", "rim_slope", "flank_slope", "top_width", "elongation"]
GEOD = Geod(ellps="WGS84")


def words(name: str) -> list[str]:
    plain = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode().lower()
    return re.findall(r"[a-z]+", plain)


def measure(src: rasterio.DatasetReader, lon: float, lat: float, prominence: float | None, dem_cfg: dict) -> dict | None:
    """The DEM measurements around one summit, or None where the DEM has no data or too little relief."""
    lo, hi = dem_cfg["radius_m"]
    radius = min(max(4 * prominence, lo), hi) if prominence else hi
    # Metres per cell at this latitude, east-west and north-south.
    cell = src.transform.a
    dx = GEOD.inv(lon, lat, lon + cell, lat)[2]
    dy = GEOD.inv(lon, lat, lon, lat + cell)[2]
    rx, ry = radius / dx * cell, radius / dy * cell
    window = from_bounds(lon - rx, lat - ry, lon + rx, lat + ry, src.transform).round_offsets().round_lengths()
    dem = src.read(1, window=window, boundless=True, fill_value=-9999).astype(float)
    dem[dem < -1000] = np.nan
    if np.isnan(dem).mean() > 0.2:
        return None

    # The summit: the highest cell near the window's centre.
    rows, cols = np.indices(dem.shape)
    cr, cc = dem.shape[0] / 2, dem.shape[1] / 2
    near = np.hypot((rows - cr) * dy, (cols - cc) * dx) <= SUMMIT_SEARCH_M
    sr, sc = np.unravel_index(np.nanargmax(np.where(near, dem, -np.inf)), dem.shape)
    z = dem[sr, sc]
    relief = z - np.nanpercentile(dem, dem_cfg["relief_floor_pct"])
    if relief < dem_cfg["min_relief_m"]:
        return None

    gy, gx = np.gradient(dem, dy, dx)
    slope = np.degrees(np.arctan(np.hypot(gx, gy)))

    def region(share: float) -> np.ndarray:
        """Ground connected to the summit and within `share` of the relief below it."""
        labels, _ = ndimage.label(np.nan_to_num(dem, nan=-1e9) >= z - share * relief, structure=np.ones((3, 3)))
        return labels == labels[sr, sc]

    top, upper = region(dem_cfg["top_band"]), region(dem_cfg["upper_band"])
    flank = upper & ~top
    ys, xs = rows[top] * dy, cols[top] * dx
    eig = np.linalg.eigvalsh(np.cov(np.vstack([xs, ys]))) if top.sum() > 2 else np.array([1.0, 1.0])
    top_area = top.sum() * dx * dy
    return {
        "relief_m": round(float(relief)),
        "top_share": round(float(top.sum() / upper.sum()), 3),
        "top_slope": round(float(np.nanmedian(slope[top])), 1),
        "rim_slope": round(float(np.nanpercentile(slope[flank], 90)), 1) if flank.any() else 0.0,
        "flank_slope": round(float(np.nanmedian(slope[flank])), 1) if flank.any() else 0.0,
        "top_width": round(float(2 * np.sqrt(top_area / np.pi) / relief), 2),
        "elongation": round(float(np.sqrt(eig.max() / max(eig.min(), 1e-9))), 2),
    }


def ramp(value: float, start: float, end: float) -> float:
    """0 at or before `start`, 1 at or beyond `end`, linear between; works for falling ramps too."""
    return min(max((value - start) / (end - start), 0.0), 1.0)


def score(props: dict, metrics: dict | None, cfg: dict) -> dict:
    """Points per landform, the evidence behind them, and the winner."""
    forms = cfg["landforms"]
    evidence = []  # (group, label, {landform: points})
    evidence.append(("prior", "prior", dict(cfg["prior"])))
    name = props["name"] if props["name"] != "Unnamed summit" else ""
    for w in words(name):
        for form, terms in cfg["names"].items():
            if w in terms:
                evidence.append(("name", f"name '{w}'", {form: terms[w]}))
    if props.get("name_code") in cfg["codes"]:
        evidence.append(("name", f"code {props['name_code']}", dict(cfg["codes"][props["name_code"]])))
    if metrics:
        for rule in cfg["rules"]:
            t = ramp(metrics[rule["metric"]], *rule["ramp"])
            if "gate" in rule:
                t *= ramp(metrics[rule["gate"]["metric"]], *rule["gate"]["ramp"])
            if t > 0:
                pts = {f: round(p * t, 2) for f, p in rule["points"].items()}
                evidence.append(("dem", f"{rule['metric']} {metrics[rule['metric']]}", pts))

    def total(groups: set[str]) -> dict[str, float]:
        out = dict.fromkeys(forms, 0.0)
        for g, _, pts in evidence:
            if g in groups:
                for f, p in pts.items():
                    out[f] += p
        return out

    def best(points: dict[str, float]) -> str:
        return max(forms, key=lambda f: (points[f], -forms.index(f)))

    scores = total({"prior", "name", "dem"})
    winner = best(scores)
    ranked = sorted(scores.values(), reverse=True)
    by_group = {g: sum(pts.get(winner, 0) for gg, _, pts in evidence if gg == g) for g in ("name", "dem")}
    source = max(by_group, key=by_group.get) if max(by_group.values()) > 0 else "default"
    named = any(g == "name" for g, _, _ in evidence)
    return {
        "landform": winner,
        "source": source,
        "margin": round(ranked[0] - ranked[1], 2),
        "scores": {f: round(v, 2) for f, v in scores.items()},
        "dem_landform": best(total({"prior", "dem"})) if metrics else "",
        "name_landform": best(total({"name"})) if named else "",
        "evidence": evidence,
    }


def main() -> None:
    cfg = tomllib.loads(CONFIG.read_text(encoding="utf-8"))
    doc = json.loads(GLYPHS.read_text(encoding="utf-8"))
    rows = []
    with tempfile.TemporaryDirectory() as tmp:
        vrt = Path(tmp) / "dem.vrt"
        subprocess.run(["gdalbuildvrt", "-q", str(vrt), *map(str, sorted(DEM_TILES.glob("*.tif")))], check=True)
        with rasterio.open(vrt) as src:
            for f in doc["features"]:
                p = f["properties"]
                if p["kind"] == "pass":  # crossing.peaks places passes on saddles; they have no summit to measure
                    p["landform"], p["landform_source"] = "pass", "dem" if p["name"] == "Unnamed pass" else "name"
                    continue
                metrics = measure(src, *f["geometry"]["coordinates"], p["prominence_m"], cfg["dem"])
                result = score(p, metrics, cfg)
                p["landform"], p["landform_source"] = result["landform"], result["source"]
                rows.append({
                    "id": p["id"], "name": p["name"], "name_code": p.get("name_code") or "",
                    "lon": f["geometry"]["coordinates"][0], "lat": f["geometry"]["coordinates"][1],
                    "elevation_m": p["elevation_m"], "prominence_m": p["prominence_m"],
                    "landform": result["landform"], "source": result["source"], "margin": result["margin"],
                    "review": "yes" if result["margin"] < cfg["review"]["min_margin"] else "",
                    "name_landform": result["name_landform"], "dem_landform": result["dem_landform"],
                    **{m: (metrics or {}).get(m, "") for m in METRICS},
                    **{f"score_{k}": v for k, v in result["scores"].items()},
                    "evidence": "; ".join(f"{label}: " + ", ".join(f"{k} {v:+g}" for k, v in pts.items())
                                          for g, label, pts in result["evidence"] if g != "prior"),
                })

    GLYPHS.write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    with REPORT.open("w", newline="", encoding="utf-8") as out:
        w = csv.DictWriter(out, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)

    counts = {f: sum(r["landform"] == f for r in rows) for f in cfg["landforms"]}
    print("landforms: " + ", ".join(f"{f} {n}" for f, n in counts.items()))
    print(f"no DEM measurement: {sum(r['dem_landform'] == '' for r in rows)}; "
          f"to review: {sum(r['review'] == 'yes' for r in rows)}")
    # How often the DEM alone agrees with a name that states a shape: a check on the DEM rules.
    stated = [r for r in rows if r["name_landform"] and r["dem_landform"]]
    agree = sum(r["name_landform"] == r["dem_landform"] for r in stated)
    print(f"names that state a shape: {len(stated)}; the DEM alone agrees on {agree}")
    for f in cfg["landforms"]:
        s = [r for r in stated if r["name_landform"] == f]
        if s:
            print(f"  {f}: {sum(r['dem_landform'] == f for r in s)} of {len(s)}")
    print(f"Wrote {GLYPHS.relative_to(REPO)} and {REPORT.relative_to(REPO)}")


if __name__ == "__main__":
    main()
