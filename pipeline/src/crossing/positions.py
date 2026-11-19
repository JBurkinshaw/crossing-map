"""Where each stop sits on its landform: candidate points by tier, and a terrain check on each (decision 0059).

Run from the repo root: uv run --project pipeline python -m crossing.positions [--only STOP ...]

Reads pipeline/seeds/stop-positions.csv, which names the part of a landform the book puts a stop at (the head of a
draw, a pass, a valley floor and so on), the built data/stops.geojson and data/places.geojson, and local caches
only: GNIS (private/cache/gazetteer/Features_20210825), GeoNames Mexico (private/cache/gazetteer/MX), NHD and the
Copernicus GLO-30 DEM. Writes review/positions/results.csv and candidates.geojson for the review mode
(site, ?review=positions on the dev server), which records the owner's verdicts in review/positions/review.csv.

Nothing here changes a stop. A stop moves only when its row in pipeline/seeds/stops.csv is edited, with reasoning.

Tiers, in the order they are trusted:

  gazetteer       A named point. GNIS's source point for "head", its primary point for "mouth". For "pass", the
                  gap nearest the way from the stop before to the stop after, within 15 km of the range's point or
                  the stop: GNIS class Gap, and GeoNames feature codes PASS, GAP and SDL in Mexico.
  gazetteer+dem   For "between" two draws: the drainage divide between their catchments, at its high cell nearest
                  the two GNIS heads.
  vector          Review aid. NHD flowlines carrying the feature's name: the upstream end farthest from the mouth.
  dem             Review aid. A head traced up the main stem, a saddle on the way through a range, the divide
                  nearest the DEM heads, or, for floor, foot, rim, high and slopes, the nearest ground within the
                  stop's area (or 5 km) that passes the check.

The DEM tiers are never published on their own: tracing a stream up from its mouth climbs the wrong branch three
times in four (review/experiments/landform-points/). The check is crossing.landform_points.check: geomorphons at
500 m and 2 km lookouts, a saddle test, and the height percentile over a window that grows with the landform.
"""

import argparse
import csv
import json
from pathlib import Path

import numpy as np

from crossing import landform_points as lf
from crossing.paths import CACHE, DATA, REPO

SEED = REPO / "pipeline" / "seeds" / "stop-positions.csv"
OUT = REPO / "review" / "positions"
GEONAMES = CACHE / "gazetteer" / "MX" / "MX.txt"
GEONAMES_GAPS = {"PASS", "GAP", "SDL"}
FIT_KM = 5.0  # how far the "dem" tier looks for fitting ground when the stop has no area


def geonames_gaps() -> list[dict]:
    out = []
    with GEONAMES.open(encoding="utf-8") as f:
        for line in f:
            c = line.rstrip("\n").split("\t")
            if c[7] in GEONAMES_GAPS:
                out.append({"name": c[1], "id": f"GeoNames {c[0]}", "point": (float(c[5]), float(c[4]))})
    return out


def gazetteer_gap(gaps: list[dict], centres: list, before, after) -> dict | None:
    """The named gap within lf.RANGE_KM of any of `centres` (the range's point and the stop) that adds least to the
    straight way from `before` to `after`."""
    near = [g for g in gaps if min(lf.km(g["point"], c) for c in centres) <= lf.RANGE_KM]
    if not near:
        return None
    direct = lf.km(before, after) if before and after else 0.0

    def detour(g) -> float:
        if not (before and after):
            return min(lf.km(g["point"], c) for c in centres)
        return lf.km(before, g["point"]) + lf.km(g["point"], after) - direct
    return min(near, key=detour)


def dem_fit(position: str, lonlat, radius_km: float) -> tuple | None:
    """The nearest cell within `radius_km` whose ground passes the check for `position`, on a 60 m grid. Landforms
    at a 500 m lookout, and the height percentile over the whole window, which is a coarse stand-in for the
    check's own window."""
    forms_ok, (lo, hi), _ = lf.EXPECT[position]
    g = lf.grid(lonlat, radius_km * 1000, 60)
    forms, _ = lf.forms_grid(g, lf.LOOKOUTS[0])
    r0, c0 = g.cell(lonlat)
    yy, xx = np.mgrid[:g.z.shape[0], :g.z.shape[1]]
    d2 = (yy - r0) ** 2 + (xx - c0) ** 2
    disc = d2 <= (radius_km * 1000 / 60) ** 2
    order = np.sort(g.z[disc])
    pct = np.searchsorted(order, g.z) / len(order) * 100
    fit = disc & np.isin(forms, list(forms_ok)) & (pct >= lo) & (pct <= hi)
    if not fit.any():
        return None
    cells = np.argwhere(fit)
    return g.lonlat(tuple(cells[np.argmin(d2[fit])]))


def load_stops() -> dict[str, dict]:
    doc = json.loads((DATA / "stops.geojson").read_text(encoding="utf-8"))
    return {f["properties"]["id"]: {**f["properties"], "lonlat": tuple(f["geometry"]["coordinates"])}
            for f in doc["features"]}


def neighbours(stops: dict, stop: dict) -> tuple:
    same = {s["sequence"]: s["lonlat"] for s in stops.values() if s["journey"] == stop["journey"]}
    return same.get(stop["sequence"] - 1), same.get(stop["sequence"] + 1)


def radius_km(stop_id: str) -> float | None:
    with (REPO / "pipeline" / "seeds" / "stops.csv").open(encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r["id"] == stop_id and r["radius_km"]:
                return float(r["radius_km"])
    return None


def resolve(row: dict, stop: dict, stops: dict, places: dict, gnis: dict, gaps: list) -> tuple[list, list]:
    """Candidate points and lines for one stop. Each candidate: (kind, lonlat, label, aid)."""
    pos, here = row["position"], stop["lonlat"]
    refs = dict(r.split(":", 1) for r in row["features"].split()) if row["features"] else {}
    ids = [int(r.split(":")[1]) for r in row["features"].split() if r.startswith("gnis:")]
    cands, lines = [], []
    if pos in ("head", "mouth") and ids:
        f = gnis[ids[0]]
        point = f["head"] if pos == "head" else f["mouth"]
        if point:
            which = "source" if pos == "head" else "primary"
            cands.append(("gazetteer", point, f"GNIS {f['id']} {f['name']}, its {which} point", False))
        if pos == "head":
            nhd = lf.nhd_head(f["name"], f["mouth"])
            if nhd:
                cands.append(("vector", nhd, f"NHD head of {f['name']}", True))
            head, stem, _ = lf.dem_head(f["mouth"])
            cands.append(("dem", head, "head traced up the main stem from GNIS's mouth", True))
            lines.append(("dem-main-stem", stem))
    elif pos == "between" and len(ids) == 2:
        a, b = gnis[ids[0]], gnis[ids[1]]
        if a["head"] and b["head"]:
            mid = ((a["head"][0] + b["head"][0]) / 2, (a["head"][1] + b["head"][1]) / 2)
            cands.append(("gazetteer", mid, "midpoint of the two GNIS heads, for context", True))
            point = lf.dem_between(a["mouth"], b["mouth"], (a["head"], b["head"]))[0]
            if point:
                cands.append(("gazetteer+dem", point, "divide between the draws, nearest the GNIS heads", False))
        point, divide = lf.dem_between(a["mouth"], b["mouth"])
        if point:
            cands.append(("dem", point, "divide between the draws, nearest the DEM heads", True))
        if divide:
            lines.append(("dem-divide", divide))
    elif pos == "pass":
        centre = places.get(refs["range"], here) if "range" in refs else here
        before, after = neighbours(stops, stop)
        gap = gazetteer_gap(gaps, [centre, here], before, after)
        if gap:
            cands.append(("gazetteer", gap["point"], f"{gap['id']} {gap['name']}", False))
        if before and after:
            point, path = lf.dem_gap(centre, before, after)
            if point:
                cands.append(("dem", point, "saddle in the range that adds least to the way through", True))
            lines.append(("least-cost-path", path))
    else:
        point = dem_fit(pos, here, radius_km(stop["id"]) or FIT_KM)
        if point:
            cands.append(("dem", point, f"nearest ground that passes the check for '{pos}'", True))
    return cands, lines


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--only", nargs="*", help="stop ids to run (default: every stop in the seed)")
    args = parser.parse_args()
    seed = list(csv.DictReader(SEED.open(encoding="utf-8")))
    if args.only:
        seed = [r for r in seed if r["stop"] in args.only]
    stops, places = load_stops(), lf.place_points()
    gnis = lf.gnis()
    gaps = [{"name": f["name"], "id": f"GNIS {f['id']}", "point": f["mouth"]}
            for f in gnis.values() if f["class"] == "Gap"] + geonames_gaps()

    rows, features = [], []
    for row in seed:
        stop = stops[row["stop"]]
        pos, here = row["position"], stop["lonlat"]
        if pos not in lf.EXPECT:
            raise SystemExit(f"{row['stop']}: unknown position {pos!r}")
        cands, lines = resolve(row, stop, stops, places, gnis, gaps)
        published, published_check = lf.check(pos, here)
        for kind, point, label, aid in [("published", here, "the stop as published", False), *cands]:
            gr, verdict = (published, published_check) if kind == "published" else lf.check(pos, point)
            features.append({"type": "Feature", "geometry": {"type": "Point", "coordinates": [*map(float, point)]},
                             "properties": {"stop": row["stop"], "kind": kind, "label": label, "aid": aid,
                                            "check": verdict, "form_500": gr["form_500"],
                                            "form_2000": gr["form_2000"],
                                            "saddle": bool(gr["saddle_500"] or gr["saddle_2000"]),
                                            "height_m": gr["height_m"], "height_pct": gr["height_pct"],
                                            "km": round(lf.km(here, point), 2)}})
        for kind, coords in lines:
            if not coords:
                continue
            geom = {"type": "MultiPoint" if kind == "dem-divide" else "LineString",
                    "coordinates": [[float(x), float(y)] for x, y in coords]}
            features.append({"type": "Feature", "geometry": geom, "properties": {"stop": row["stop"], "kind": kind}})
        rows.append({"stop": row["stop"], "journey": stop["journey"], "seq": stop["sequence"], "name": stop["name"],
                     "position": pos, "lon": here[0], "lat": here[1], "check": published_check,
                     "flagged": str(not published_check.startswith("ok")).lower(), "candidates": len(cands),
                     "note": row["note"]})
        print(f"{row['stop']:28} {pos:8} {published_check:40} "
              + ", ".join(f"{k} {lf.km(here, p):.1f} km" for k, p, _, _ in cands))

    OUT.mkdir(parents=True, exist_ok=True)
    if args.only:
        old = {r["stop"]: r for r in csv.DictReader((OUT / "results.csv").open(encoding="utf-8"))}
        old.update({r["stop"]: r for r in rows})
        rows = [old[r["stop"]] for r in csv.DictReader(SEED.open(encoding="utf-8")) if r["stop"] in old]
        kept = [f for f in json.loads((OUT / "candidates.geojson").read_text())["features"]
                if f["properties"]["stop"] not in args.only]
        features = kept + features
    with (OUT / "results.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    write_geojson(OUT / "candidates.geojson", features)
    flagged = sum(r["flagged"] == "true" for r in rows)
    print(f"{len(rows)} stops, {flagged} flagged: review/positions/results.csv, candidates.geojson")


def write_geojson(path: Path, features: list) -> None:
    for f in features:
        g = f["geometry"]
        if g["type"] == "Point":
            g["coordinates"] = [round(v, 5) for v in g["coordinates"]]
        else:
            g["coordinates"] = [[round(x, 5), round(y, 5)] for x, y in g["coordinates"]]
    path.write_text(json.dumps({"type": "FeatureCollection", "features": features}, ensure_ascii=False) + "\n",
                    encoding="utf-8")


if __name__ == "__main__":
    main()
