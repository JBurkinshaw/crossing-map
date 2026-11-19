"""Figures for the landform-points experiment: one hillshade map per J1 stop with a position, and the calibration.

Run from the repo root, after crossing.landform_points:
    uv run --project pipeline --with matplotlib python -m crossing.landform_points_images

Reads review/experiments/landform-points/results.csv, points.geojson and calibration.csv. Writes img/ beside them.
The hillshade is the Copernicus GLO-30 DEM on the experiment's transverse Mercator grid (60 m), lit from the
north-west at 45 degrees.
"""

import csv
import json
import math

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

from crossing.landform_points import HEAD_AREAS, OUT, grid, km  # noqa: E402

STYLE = {
    "original": dict(marker="X", color="#b8322a", s=140, label="original stop"),
    "updated": dict(marker="o", color="#111111", s=110, label="stop after review", facecolors="none", linewidths=2.2),
    "gazetteer": dict(marker="s", color="#2b5fb3", s=70, label="tier 1: gazetteer (GNIS)"),
    "vector": dict(marker="P", color="#7a3fa0", s=90, label="tier 2: NHD"),
    "dem": dict(marker="^", color="#d9801e", s=90, label="tier 3: DEM"),
    "dem+gazetteer": dict(marker="D", color="#2f8a3b", s=70, label="DEM divide aimed at GNIS heads"),
}
LINES = {
    "dem-main-stem": dict(color="#d9801e", lw=1.4, label="DEM main stem from the mouth"),
    "least-cost-path": dict(color="#555555", lw=1.2, ls="--", label="wolf's least-cost path"),
}


def hillshade(z: np.ndarray, res: float) -> np.ndarray:
    dy, dx = np.gradient(z, res)
    slope = np.arctan(np.hypot(dx, dy))
    aspect = np.arctan2(-dx, dy)
    az, alt = math.radians(315), math.radians(45)
    return np.clip(np.sin(alt) * np.cos(slope) + np.cos(alt) * np.sin(slope) * np.cos(az - aspect), 0, 1)


def draw_stop(row: dict, shapes: list[dict], out) -> None:
    pts = {k: tuple(map(float, row[k].split(",")))[::-1] for k in STYLE if row.get(k)}
    lons = [p[0] for p in pts.values()]
    lats = [p[1] for p in pts.values()]
    centre = ((min(lons) + max(lons)) / 2, (min(lats) + max(lats)) / 2)
    span = max(km((min(lons), centre[1]), (max(lons), centre[1])), km((centre[0], min(lats)), (centre[0], max(lats))))
    half = max(4000, span * 1000 * 0.75 + 2500)
    g = grid(centre, half, 60)
    fig, ax = plt.subplots(figsize=(8, 8), dpi=150)
    extent = (-half, half, -half, half)
    ax.imshow(hillshade(g.z, 60), cmap="gray", extent=extent, vmin=0, vmax=1)
    ax.imshow(g.z, cmap="terrain", alpha=0.35, extent=extent)
    ax.contour(np.flipud(g.z), levels=np.arange(1000, 3000, 100), colors="#6b5b45", linewidths=0.3,
               extent=extent, origin="lower")

    def xy(lonlat):
        return g.fwd.transform(*lonlat)

    for f in shapes:
        kind = f["properties"]["kind"]
        if f["properties"]["stop"] != row["stop"]:
            continue
        if kind in LINES:
            x, y = zip(*(xy(p) for p in f["geometry"]["coordinates"]), strict=True)
            ax.plot(x, y, **LINES[kind])
        elif kind == "dem-divide":
            x, y = zip(*(xy(p) for p in f["geometry"]["coordinates"]), strict=True)
            ax.scatter(x, y, s=2, color="#2f8a3b", alpha=0.5, label="DEM divide between the draws")
    for k, p in pts.items():
        ax.scatter(*xy(p), zorder=5, **STYLE[k])
    ax.set_xlim(-half, half)
    ax.set_ylim(-half, half)
    ax.set_xticks([])
    ax.set_yticks([])
    # A 2 km scale bar, bottom left.
    ax.plot([-half * 0.9, -half * 0.9 + 2000], [-half * 0.9] * 2, color="k", lw=3)
    ax.text(-half * 0.9 + 1000, -half * 0.86, "2 km", ha="center")
    checks = "\n".join(f"{k}: {row[f'check_{k}']}" for k in STYLE if row.get(f"check_{k}"))
    ax.set_title(f"{row['stop']} (stop {row['seq']}): position '{row['position']}'", fontsize=11)
    ax.text(0.01, 0.99, checks, transform=ax.transAxes, va="top", fontsize=7,
            bbox=dict(facecolor="white", alpha=0.85, edgecolor="none"))
    ax.legend(loc="lower right", fontsize=7, framealpha=0.9)
    fig.tight_layout()
    fig.savefig(out / f"{row['stop']}.png")
    plt.close(fig)


def draw_calibration(rows: list[dict], out) -> None:
    fig, ax = plt.subplots(figsize=(7, 4), dpi=150)
    bins = np.arange(0, 16, 0.5)
    for area in HEAD_AREAS:
        errs = [float(r[f"err_km_{area}"]) for r in rows]
        ax.hist(errs, bins=bins, histtype="step", lw=1.6, label=f"{area} km² (median {np.median(errs):.1f} km)")
    ax.set_xlabel("DEM head to GNIS head, km")
    ax.set_ylabel("GNIS features")
    ax.set_title(f"Tier 3 heads against GNIS heads, {len(rows)} valleys, streams and arroyos around J1", fontsize=10)
    ax.legend(title="channel-head area", fontsize=8)
    fig.tight_layout()
    fig.savefig(out / "calibration.png")
    plt.close(fig)


def main() -> None:
    out = OUT / "img"
    out.mkdir(exist_ok=True)
    rows = list(csv.DictReader((OUT / "results.csv").open(encoding="utf-8")))
    shapes = json.loads((OUT / "points.geojson").read_text())["features"]
    for row in rows:
        if row["position"] != "none":
            draw_stop(row, shapes, out)
            print(f"img/{row['stop']}.png")
    if (OUT / "calibration.csv").exists():
        draw_calibration(list(csv.DictReader((OUT / "calibration.csv").open(encoding="utf-8"))), out)
        print("img/calibration.png")


if __name__ == "__main__":
    main()
