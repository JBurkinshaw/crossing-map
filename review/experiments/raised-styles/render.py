"""Raised-view style experiments: one test box over the Sierra de los Pilares de Teras drawn in several looks, after
the oblique maps on Carl Churchill's "Variety in hachure" (docs/inspiration/churchill.md). Shown side by side in a
lab section, since removed (decision 0040 records the outcome).

Run from the repo root. It makes no network requests: it reads the Copernicus tiles, the production fine hachure
cache and the base map's sources, as crossing.plan_oblique does.
    uv run --project pipeline python review/experiments/raised-styles/render.py [name ...]
Writes site/public/lab/raised/<name>.webp. Intermediate files go to private/cache/raised-styles/.

Every look uses crossing.plan_oblique's own projection (Grid, build_strip): each point moves north by LEAN times its
height above the lowest ground, and ground hidden by nearer ground is cut away. A look changes only the lean, which
strokes are drawn and how. The strokes of the new looks are traced here, down the fall line of the same smoothed
30 m DEM, instead of by Huffman's generator, so their density and weight can follow the light.
Coordinates: UTM zone 12N (EPSG:32612) on WGS 84. Light from the north-west (azimuth 315, altitude 45 degrees).
"""

import json
import math
import sys
import tempfile
from pathlib import Path

import numpy as np
import rasterio
import rasterio.transform
import shapely
from PIL import Image, ImageDraw, ImageFont
from rasterio.windows import from_bounds
from scipy.ndimage import gaussian_filter, map_coordinates, maximum_filter, minimum_filter
from scipy.spatial import cKDTree

import crossing.plan_oblique as po
from crossing.hachures import prepare_dem
from crossing.paths import CACHE, DATA

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "site" / "public" / "lab" / "raised"
WORK = CACHE / "raised-styles"
# The test boxes, 36 by 34 km each. pilares: the Pilares, El Tigre, and the Bavispe valley at Colonia Morelos and
# Colonia Oaxaca, all in Mexico. border: the Guadalupe Mountains and Cloverdale, across the border, so that both
# land cover sources show. A look for the border box is named border-<look>.
BOXES = {
    "pilares": (662_000, 3_380_000, 698_000, 3_414_000),
    "border": (677_000, 3_451_000, 713_000, 3_485_000),
}
SOUTH = 7_000  # ground this far south of the box can rise into view at a lean of 4
MPP = 22.5  # metres per output pixel: 1600 px across, about zoom 11.5 at 30.7 N
SS = 3  # supersampling: drawn at 3 times the size, then reduced, for smooth thin lines
CELL = po.CELL
AZIMUTH, ALTITUDE = 315, 45
WALL = 500  # block diagram: metres of ground below the lowest point shown in the south wall
GENERALISE = 4  # cells (120 m): the extra smoothing of the surface strokes are placed and lit by
FONT = "/System/Library/Fonts/Supplemental/Georgia Italic.ttf"
TOWNS = ("Colonia Morelos", "Colonia Oaxaca", "El Tigre", "Ojito", "Batepito", "Cloverdale")
RANGES = ("Sierra de los Pilares de Teras", "Sierra de la Cabellera", "Guadalupe Mountains")


# ---- Ground ---------------------------------------------------------------------------------------------------


def dem(name: str, bounds: tuple[float, ...]) -> Path:
    path = WORK / f"{name}.tif"
    if not path.exists():
        WORK.mkdir(parents=True, exist_ok=True)
        prepare_dem(bounds, CELL, path)
    return path


def crop_south(src_path: Path, south: float) -> Path:
    """A copy of a DEM that starts at `south`, for the block diagram, whose ground ends at the box's south edge."""
    out = WORK / f"{src_path.stem}-from-{int(south)}.tif"
    if not out.exists():
        with rasterio.open(src_path) as src:
            b = src.bounds
            window = from_bounds(b.left, south, b.right, b.top, transform=src.transform).round_offsets().round_lengths()
            profile = src.profile | {
                "height": window.height,
                "width": window.width,
                "transform": src.window_transform(window),
            }
            data = src.read(1, window=window)
        with rasterio.open(out, "w", **profile) as dst:
            dst.write(data, 1)
    return out


class Fields:
    """Slope, aspect, light and local relief on a Grid's south-to-north DEM."""

    def __init__(self, g: po.Grid, sigma: float = GENERALISE):
        self.g = g
        # Light and fall lines come from a further-smoothed surface, so strokes follow the main faces, as an
        # engraver generalises, not every gully.
        gy, gx = np.gradient(gaussian_filter(g.Z, sigma), CELL)
        self.gx, self.gy = gx, gy
        s = np.arctan(np.hypot(gx, gy))
        self.slope = np.degrees(s)
        aspect = np.arctan2(-gx, -gy)  # downhill direction, clockwise from north
        z = math.radians(90 - ALTITUDE)
        self.light = np.clip(
            math.cos(z) * np.cos(s) + math.sin(z) * np.sin(s) * np.cos(math.radians(AZIMUTH) - aspect), 0, 1
        )
        self.north = np.cos(aspect)  # 1 on slopes facing north
        low, high = minimum_filter(g.Z, 67), maximum_filter(g.Z, 67)  # about 1 km either side
        self.relief = g.Z - low
        self.height_share = (g.Z - low) / np.maximum(high - low, 1)

    def at(self, raster: np.ndarray, x: np.ndarray, y: np.ndarray) -> np.ndarray:
        g = self.g
        return map_coordinates(raster, [(y - g.y0) / CELL - 0.5, (x - g.x0) / CELL - 0.5], order=1, mode="nearest")


def seeds(area: tuple[float, ...], spacing: float, rng: np.random.Generator) -> tuple[np.ndarray, np.ndarray]:
    """Points on a jittered grid `spacing` metres apart."""
    xs = np.arange(area[0], area[2], spacing)
    ys = np.arange(area[1], area[3], spacing)
    x, y = (a.ravel() for a in np.meshgrid(xs, ys))
    return x + rng.uniform(0, spacing, x.size), y + rng.uniform(0, spacing, y.size)


def fall_lines(f: Fields, x: np.ndarray, y: np.ndarray, length: np.ndarray, step: float = 10) -> list[np.ndarray]:
    """From each seed, a line `length` metres long down the fall line."""
    n = int(length.max() // step) + 1
    px, py = [x.copy()], [y.copy()]
    for _ in range(n - 1):
        gx, gy = f.at(f.gx, x, y), f.at(f.gy, x, y)
        norm = np.maximum(np.hypot(gx, gy), 1e-6)
        x, y = x - step * gx / norm, y - step * gy / norm
        px.append(x)
        py.append(y)
    px, py = np.array(px).T, np.array(py).T
    keep = np.maximum((length // step).astype(int) + 1, 2)
    return [np.column_stack([px[i, :k], py[i, :k]]) for i, k in enumerate(keep)]


# ---- The view -------------------------------------------------------------------------------------------------


class View:
    """One lean: the Grid, the shifted line work from crossing.plan_oblique.build_strip, and the screen."""

    def __init__(
        self,
        name: str,
        dem_path: Path,
        base: float,
        lean: float,
        core: tuple[float, ...],
        window: tuple[float, ...],
        lines: list,
        mexico,
    ):
        po.LEAN = lean
        self.lean, self.core, self.window = lean, core, window
        self.g = po.Grid(dem_path, base)
        self.f = Fields(self.g)
        cache = WORK / f"lines-{name}.geojsonl"
        if not cache.exists():
            strip = {"core": core, "tiles": fine_tiles(core), "bounds": None}
            po.build_strip(strip, dem_path, base, lines, mexico, cache)
        self.lines: dict[str, list] = {}
        for row in cache.read_text().splitlines():
            feat = json.loads(row)
            if feat["geometry"]["type"] != "LineString":
                continue
            xy = np.array(feat["geometry"]["coordinates"])
            ex, ey = po.to_utm(xy[:, 0], xy[:, 1])
            self.lines.setdefault(feat["properties"]["kind"], []).append(
                (feat["properties"], np.column_stack([ex, ey]))
            )

    def project(self, xy: np.ndarray) -> list[np.ndarray]:
        """Runs of a flat line that are in the core and not hidden, shifted."""
        po.LEAN = self.lean
        yp, shown = self.g.project(xy[:, 0], xy[:, 1], self.core)
        edges = np.flatnonzero(np.diff(np.concatenate([[0], shown.astype(np.int8), [0]])))
        return [
            np.column_stack([xy[a:b, 0], yp[a:b]]) for a, b in zip(edges[::2], edges[1::2], strict=True) if b - a >= 2
        ]

    def stretch(self, xy: np.ndarray) -> np.ndarray:
        return self.f.at(self.g.stretch, xy[:, 0], xy[:, 1])

    def surface(self) -> tuple[np.ndarray, np.ndarray]:
        """For each output pixel, the DEM row and column seen there. Row -1 is sky; -2 is below the front edge."""
        g, (wx0, wy0, wx1, wy1) = self.g, self.window
        w, h = round((wx1 - wx0) / MPP), round((wy1 - wy0) / MPP)
        ys = wy1 - (np.arange(h) + 0.5) * MPP
        cols = np.clip(np.round((wx0 + (np.arange(w) + 0.5) * MPP - g.x0) / CELL - 0.5).astype(int), 0, len(g.xs) - 1)
        # Clip the ground to the core's south edge, so the block's wall shows below it.
        first = max(0, int(np.searchsorted(g.ys, self.core[1])))
        runmax = np.maximum.accumulate(g.shifted[first:], axis=0)
        rows = np.empty((h, w), dtype=int)
        asc = ys[::-1]
        for j, c in enumerate(cols):
            r = np.searchsorted(runmax[:, c], asc)
            r = np.where(r >= runmax.shape[0], -1, r + first)
            r = np.where(asc < g.shifted[first, c], -2, r)
            rows[:, j] = r[::-1]
        return rows, cols


def fine_tiles(core: tuple[float, ...]) -> list[tuple[str, tuple[float, ...]]]:
    """The production fine tiles (name, core) that overlap `core`."""
    out = []
    for path in sorted(po.FINE.glob("*-split.geojson")):
        name = path.name.removesuffix("-split.geojson")
        x, y = (int(v[:-1]) * 1000 for v in name.split("-"))
        if x < core[2] and x + po.TILE > core[0] and y < core[3] and y + po.TILE > core[1]:
            out.append((name, (x, y, x + po.TILE, y + po.TILE)))
    return out


# ---- Drawing --------------------------------------------------------------------------------------------------


def rgb(hex_: str) -> tuple[int, int, int]:
    return tuple(int(hex_[i : i + 2], 16) for i in (1, 3, 5))


def mix(ink: str, paper: str, a: float) -> tuple[int, int, int]:
    i, p = rgb(ink), rgb(paper)
    return tuple(round(p[k] + (i[k] - p[k]) * a) for k in range(3))


class Canvas:
    def __init__(self, view: View, paper: str):
        wx0, wy0, wx1, wy1 = view.window
        self.view, self.paper = view, paper
        self.size = (round((wx1 - wx0) / MPP), round((wy1 - wy0) / MPP))
        self.img = Image.new("RGB", (self.size[0] * SS, self.size[1] * SS), paper)
        self.d = ImageDraw.Draw(self.img)
        self.k = SS / MPP

    def pts(self, xy: np.ndarray) -> np.ndarray:
        wx0, _, _, wy1 = self.view.window
        return np.column_stack([(xy[:, 0] - wx0) * self.k, (wy1 - xy[:, 1]) * self.k])

    def line(self, xy: np.ndarray, width: float, colour) -> None:
        p = self.pts(xy)
        self.d.line([tuple(q) for q in p], fill=colour, width=max(1, round(width * SS)), joint="curve")

    def taper(self, xy: np.ndarray, top: float, bottom: float, colour) -> None:
        """A stroke whose width runs from `top` to `bottom` pixels: a wedge when bottom is 0."""
        p = self.pts(xy)
        if len(p) < 2:
            return
        d = np.gradient(p, axis=0)
        n = np.column_stack([-d[:, 1], d[:, 0]]) / np.maximum(np.hypot(*d.T), 1e-6)[:, None]
        w = np.linspace(top, bottom, len(p))[:, None] * SS / 2
        ring = np.concatenate([p + n * w, (p - n * w)[::-1]])
        self.d.polygon([tuple(q) for q in ring], fill=colour)

    def dot(self, xy: tuple[float, float], r: float, colour) -> None:
        ((x, y),) = self.pts(np.array([xy]))
        self.d.ellipse([x - r * SS, y - r * SS, x + r * SS, y + r * SS], fill=colour)

    def tone(self, shade: np.ndarray, ink: str, strength: float, mask: np.ndarray | None = None) -> None:
        """Multiply a tone (0 = none, 1 = full ink) over the paper."""
        a = np.clip(shade * strength, 0, 1)
        if mask is not None:
            a = np.where(mask, a, 0)
        ink_rgb = np.array(rgb(ink), dtype=float)
        layer = 255 - (255 - ink_rgb)[None, None, :] * a[:, :, None]
        img = Image.fromarray(layer.astype(np.uint8)).resize(self.img.size, Image.BILINEAR)
        self.img = Image.fromarray(
            (np.asarray(self.img, dtype=float) * np.asarray(img, dtype=float) / 255).astype(np.uint8)
        )
        self.d = ImageDraw.Draw(self.img)

    def underlay(self, colours: np.ndarray) -> None:
        """Replace the paper with an image (output pixels, RGB), enlarged without smoothing so classes keep edges."""
        self.img = Image.fromarray(colours.astype(np.uint8)).resize(self.img.size, Image.NEAREST)
        self.d = ImageDraw.Draw(self.img)

    def label(self, xy: tuple[float, float], text: str, size: float, colour, spacing: float = 0) -> None:
        ((x, y),) = self.pts(np.array([xy]))
        font = ImageFont.truetype(FONT, round(size * SS))
        if spacing:
            text = (" " * int(spacing)).join(text)
        box = self.d.textbbox((0, 0), text, font=font)
        tx, ty = x - (box[2] - box[0]) / 2, y + 4 * SS
        for dx, dy in ((-2, 0), (2, 0), (0, -2), (0, 2)):
            self.d.text((tx + dx, ty + dy), text, font=font, fill=self.paper)
        self.d.text((tx, ty), text, font=font, fill=colour)

    def save(self, name: str) -> Path:
        OUT.mkdir(parents=True, exist_ok=True)
        path = OUT / f"{name}.webp"
        self.img.resize(self.size, Image.LANCZOS).save(path, quality=88, method=6)
        return path


# ---- Features -------------------------------------------------------------------------------------------------


def places() -> list[tuple[str, str, tuple[float, float]]]:
    out = []
    for feat in json.loads((DATA / "places.geojson").read_text(encoding="utf-8"))["features"]:
        name = feat["properties"].get("name")
        if name in TOWNS or name in RANGES:
            x, y = po.to_utm(*feat["geometry"]["coordinates"][:2])
            out.append((name, "range" if name in RANGES else "town", (x, y)))
    return out


def label_places(c: Canvas, v: View, colour, town_mark=None) -> None:
    for name, kind, (x, y) in places():
        w = v.window
        if not (w[0] < x < w[2] and max(w[1], v.core[1]) < y < w[3]):
            continue
        yp = y + (v.f.at(v.g.Z, np.array([x]), np.array([y]))[0] - v.g.base) * v.lean
        if kind == "town":
            (town_mark or (lambda c, p: c.dot(p, 2.2, colour)))(c, (x, yp))
            c.label((x, yp), name, 12.5, colour)
        else:
            c.label((x, yp), name.upper(), 11, colour, spacing=1)


def draw_kind(c: Canvas, v: View, kind: str, width, colour, test=lambda p: True) -> None:
    for props, xy in v.lines.get(kind, []):
        if test(props):
            c.line(xy, width(props) if callable(width) else width, colour)


def visible_pieces(v: View, strokes: list[np.ndarray], fold: float = po.FOLD) -> list[tuple[int, np.ndarray]]:
    """Each stroke's shown runs, shifted, with its index; strokes on ground squeezed below `fold` are dropped."""
    out = []
    for i, s in enumerate(strokes):
        ok = v.stretch(s) >= fold
        if ok.mean() < 0.6:
            continue
        for run in v.project(s):
            out.append((i, run))
    return out


def light_at(v: View, xy: np.ndarray) -> np.ndarray:
    return v.f.at(v.f.light, xy[:, 0], xy[:, 1])


# ---- The looks ------------------------------------------------------------------------------------------------


def production(c: Canvas, v: View, ink="#2e2010", tone: float = 0) -> None:
    """The Raised view as the site draws it (site/src/map/relief.ts, raisedLayers) at zoom 11.5."""
    paper = c.paper
    if tone:
        rows, cols = v.surface()
        shade = np.where(rows >= 0, 1 - v.f.light[np.maximum(rows, 0), cols[None, :]], 0)
        c.tone(shade, "#5a4a36", tone)
    draw_kind(c, v, "contour", 0.4, mix("#b0622e", paper, 0.45))
    zoom_w = 0.8 + 0.2 * 1.5 / 3
    zoom_o = 0.55 + 0.45 * 1.5 / 3
    rad = math.radians
    for props, xy in v.lines.get("stroke", []):
        if props["Rand"] >= 7:
            continue
        s, a = props["Slope"], props["Aspect"]
        zen = rad(45)
        lit = math.cos(zen) * math.cos(rad(s)) + math.sin(zen) * math.sin(rad(s)) * math.cos(rad(315 - a))
        shade = 1 - max(0, min(1, lit))
        t = min(1, max(0, (s - 10) / 30))
        # byShade(amount) in relief.ts: between 1 - amount and 1 + 1.5 * amount.
        shade_w, shade_o = 1 - 0.4 + 0.4 * 2.5 * shade, 1 - 0.6 + 0.6 * 2.5 * shade
        w = 0.9 * (0.25 + t * 1.05) * shade_w * (1 + 0.5 * (-0.4 + t * 0.65)) * zoom_w
        o = zoom_o * min(1, 0.65 * shade_o * (1 + 0.5 * (-0.6 + t * 1.05)))
        c.line(xy, w + 0.15, mix(ink, paper, o))
    draw_kind(
        c,
        v,
        "ridge",
        lambda p: 0.5 + 0.6 * min(1, max(0, (p["rel"] - 100) / 200)),
        mix("#2b2118", paper, 0.7),
        lambda p: p["rel"] >= 160,
    )
    draw_kind(c, v, "crest", 0.9, mix("#2b2118", paper, 0.8))
    draw_kind(c, v, "stream", lambda p: 0.6 + (p["ord"] - 3) * 0.32, mix("#6f8796", paper, 0.6))
    draw_kind(c, v, "road", 0.8, mix("#7a5a3a", paper, 0.8))
    label_places(c, v, "#2b2118")


def current(v: View) -> Canvas:
    c = Canvas(v, "#ece2c6")
    production(c, v)
    return c


def steeper_toned(v: View) -> Canvas:
    c = Canvas(v, "#f2ead3")
    production(c, v, tone=0.55)
    return c


def alpha(v: View, rng: np.random.Generator) -> Canvas:
    """After Tau Rho Alpha's Atlas of Oblique Maps (USGS I-1799, 1988): long fall-line strokes packed on the faces
    away from the light and thinned on the lit ones, level dashes on the flats, heavy crests."""
    ink, paper = "#1e1e1c", "#fbfaf4"
    c = Canvas(v, paper)
    f = v.f
    x, y = seeds(v.core, 52, rng)
    slope, light = f.at(f.slope, x, y), f.at(f.light, x, y)
    keep = (slope > 5) & (
        rng.random(x.size) < np.clip(0.04 + 1.3 * (1 - light) ** 2.2, 0, 1) * np.clip(slope / 14, 0, 1)
    )
    x, y, light = x[keep], y[keep], light[keep]
    strokes = fall_lines(f, x, y, rng.uniform(140, 320, x.size))
    for i, run in visible_pieces(v, strokes):
        dark = 1 - light[i]
        c.taper(run, 0.3 + 0.9 * dark, 0.2 + 0.2 * dark, ink)
    # Level dashes on the flats: rows 110 m apart in the ground, each a run of dashes with gaps.
    for row in np.arange(v.core[1], v.core[3], 110):
        xs = np.arange(v.core[0], v.core[2], 10.0)
        ys = np.full_like(xs, row + rng.uniform(-20, 20))
        flat = (f.at(f.slope, xs, ys) < 3.5) & (np.sin(xs / rng.uniform(35, 60) + rng.uniform(0, 6)) > -0.1)
        flat &= rng.random() < 0.9
        edges = np.flatnonzero(np.diff(np.concatenate([[0], flat.astype(np.int8), [0]])))
        for a, b in zip(edges[::2], edges[1::2], strict=True):
            if b - a >= 3:
                for run in v.project(np.column_stack([xs[a:b], ys[a:b]])):
                    c.line(run, 0.5, mix(ink, paper, 0.75))
    draw_kind(c, v, "stream", lambda p: 0.7 + (p["ord"] - 3) * 0.25, "#2f6f8f")
    draw_kind(c, v, "road", 0.6, ink)
    draw_kind(c, v, "crest", 1.3, ink)
    label_places(c, v, ink)
    return c


def guanabara(v: View, rng: np.random.Generator) -> Canvas:
    """After Frank R. Holmes's Estado da Guanabara (1965), in Percy Lau's manner: each hill a fan of short strokes
    from its crest, heavy on the shaded side, a firm outline round every crest, stippled lowlands."""
    ink, paper = "#232323", "#f5f3ed"
    c = Canvas(v, paper)
    f = v.f
    # Stipple first, so the hills' strokes lie over it.
    x, y = seeds(v.core, 95, rng)
    lowland = (f.at(f.slope, x, y) < 4) & (f.at(f.relief, x, y) < 40)
    for xy in np.column_stack([x[lowland], y[lowland]]):
        for run in v.project(np.array([xy, xy + [1, 0]])):
            c.dot(tuple(run[0]), 0.55, mix(ink, paper, 0.7))
    x, y = seeds(v.core, 58, rng)
    share, slope, light = f.at(f.height_share, x, y), f.at(f.slope, x, y), f.at(f.light, x, y)
    keep = (slope > 7) & (f.at(f.relief, x, y) > 50) & (share > 0.55)
    keep &= rng.random(x.size) < np.clip(0.1 + 1.1 * (1 - light) ** 1.8, 0, 1)
    x, y, light = x[keep], y[keep], light[keep]
    strokes = fall_lines(f, x, y, rng.uniform(80, 170, x.size) * (0.6 + 0.8 * (1 - light)))
    for i, run in visible_pieces(v, strokes):
        dark = 1 - light[i]
        c.taper(run, 0.4 + 1.1 * dark, 0.1, ink)
    draw_kind(c, v, "stream", 0.6, ink)
    draw_kind(c, v, "road", 0.5, mix(ink, paper, 0.7))
    draw_kind(c, v, "ridge", lambda p: 0.6 + 0.6 * min(1, (p["rel"] - 100) / 300), ink)
    draw_kind(c, v, "crest", 1.4, ink)
    label_places(c, v, ink)
    return c


def trentino(v: View, rng: np.random.Generator) -> Canvas:
    """After the American Geographical Society's block diagram of the Trentino (1918): pencil strokes, heavy at the
    top and fading downhill, mostly on the shaded faces; blue water and red roads on tan paper; the block's south
    wall cut through the ground, with a line every 100 m of height."""
    ink, paper = "#3b3732", "#e4d5b3"
    c = Canvas(v, paper)
    f, g = v.f, v.g
    rows, cols = v.surface()
    # The wall: below the ground's front edge, down to WALL metres under the lowest ground.
    wx0, wy0, wx1, wy1 = v.window
    ys = wy1 - (np.arange(rows.shape[0]) + 0.5) * MPP
    first = int(np.searchsorted(g.ys, v.core[1]))
    front = g.shifted[first, cols]
    floor = v.core[1] + (-WALL) * v.lean
    wall = (rows == -2) & (ys[:, None] >= floor)
    height = g.base + (ys[:, None] - v.core[1]) / v.lean  # the height each wall pixel shows
    strata = (np.abs(((height + 1e4) % 100) - 50) > 46) & wall
    c.tone(np.where(wall, 0.18, 0) + np.where(strata, 0.35, 0), ink, 1)
    # The wall's edges: the ground's profile on top, the floor, and the two sides.
    profile = np.column_stack([g.xs[cols], front])
    keep = (profile[:, 0] >= v.core[0]) & (profile[:, 0] <= v.core[2])
    c.line(profile[keep], 1.1, ink)
    c.line(np.array([[v.core[0], floor], [v.core[2], floor]]), 1.1, ink)
    for side in (v.core[0] + MPP / 2, v.core[2] - MPP / 2):
        top = front[np.argmin(np.abs(g.xs[cols] - side))]
        c.line(np.array([[side, floor], [side, top]]), 1.1, ink)
    x, y = seeds(v.core, 54, rng)
    slope, light = f.at(f.slope, x, y), f.at(f.light, x, y)
    keep = (slope > 6) & (rng.random(x.size) < np.clip(1.6 * (1 - light) - 0.45, 0.03, 1) * np.clip(slope / 16, 0, 1))
    x, y, light = x[keep], y[keep], light[keep]
    strokes = fall_lines(f, x, y, rng.uniform(140, 420, x.size))
    for i, run in visible_pieces(v, strokes):
        dark = 1 - light[i]
        c.taper(run, 0.4 + 1.2 * dark, 0.1, mix(ink, paper, 0.5 + 0.45 * dark))
    draw_kind(c, v, "ridge", 0.6, ink)
    draw_kind(c, v, "crest", 0.8, ink)
    draw_kind(c, v, "stream", lambda p: 1.0 + (p["ord"] - 3) * 0.45, "#6aa3a6")
    draw_kind(c, v, "road", 1.2, "#c9473a")
    label_places(c, v, ink)
    return c


def comic(v: View, rng: np.random.Generator) -> Canvas:
    """After Charles H. Owens's Panama Canal (Los Angeles Times, 1928): the "comic-book" strokes. Faces away from the
    light become solid black flames, middle tones short hatching, lit faces blank paper; heavy crests."""
    ink, paper = "#151515", "#ece8dc"
    c = Canvas(v, paper)
    f = v.f
    # Middle tones.
    x, y = seeds(v.core, 64, rng)
    slope, light = f.at(f.slope, x, y), f.at(f.light, x, y)
    keep = (slope > 6) & (light > 0.4) & (light < 0.68) & (rng.random(x.size) < 0.45)
    x, y = x[keep], y[keep]
    for _, run in visible_pieces(v, fall_lines(f, x, y, rng.uniform(70, 150, x.size))):
        c.line(run, 0.6, ink)
    # Shadow flames: wide at the top, to a point downhill.
    x, y = seeds(v.core, 66, rng)
    slope, light = f.at(f.slope, x, y), f.at(f.light, x, y)
    keep = (slope > 6) & (light < 0.52)
    x, y, light = x[keep], y[keep], light[keep]
    strokes = fall_lines(f, x, y, rng.uniform(160, 420, x.size) * (1.4 - light))
    for i, run in visible_pieces(v, strokes, fold=0.3):
        c.taper(run, 1.6 + 5.5 * (0.52 - light[i]) / 0.52, 0, ink)
    # Lowland hatching: a few level strokes on the flats.
    x, y = seeds(v.core, 220, rng)
    flat = (f.at(f.slope, x, y) < 3) & (rng.random(x.size) < 0.6)
    for xy in np.column_stack([x[flat], y[flat]]):
        half = rng.uniform(50, 110)
        for run in v.project(np.array([xy - [half, 0], xy, xy + [half, 0]])):
            c.line(run, 0.6, mix(ink, paper, 0.8))
    draw_kind(c, v, "ridge", 1.2, ink)
    draw_kind(c, v, "crest", 1.9, ink)
    # Rivers as two inked banks with paper between.
    draw_kind(c, v, "stream", lambda p: 2.4 + (p["ord"] - 3) * 0.6, ink)
    draw_kind(c, v, "stream", lambda p: 1.0 + (p["ord"] - 3) * 0.6, paper)
    for _, xy in v.lines.get("road", []):
        d = np.concatenate([[0], np.cumsum(np.hypot(*np.diff(xy, axis=0).T))])
        on = (d // 160) % 2 == 0
        edges = np.flatnonzero(np.diff(np.concatenate([[0], on.astype(np.int8), [0]])))
        for a, b in zip(edges[::2], edges[1::2], strict=True):
            if b - a >= 2:
                c.line(xy[a:b], 1.1, ink)
    label_places(c, v, ink)
    return c


# Vegetation by height and aspect, after Brown's biotic communities of the Madrean sky islands (Brown, ed., Biotic
# Communities: Southwestern United States and Northwestern Mexico, 1994): desert scrub and semi-desert grassland
# below about 1,250 m, Madrean oak woodland above, pine-oak forest above about 1,800 m, each reaching about 150 m
# lower on slopes facing north; cottonwood and sycamore along the larger streams. A judgement call for the lab only.
OAK, PINE, NORTH_DROP, RIPARIAN = 1_250, 1_800, 150, 150


def pine(c: Canvas, p, ink, paper, s=1.0) -> None:
    x, y = c.pts(np.array([p]))[0]
    h, w = 16 * SS * s, 4.2 * SS * s
    c.d.polygon(
        [(x, y - h), (x - w, y - h * 0.15), (x + w, y - h * 0.15)], fill=paper, outline=ink, width=max(1, SS // 2)
    )
    c.d.line([(x, y - h * 0.15), (x, y)], fill=ink, width=SS)


def oak(c: Canvas, p, ink, paper, rng, s=1.0) -> None:
    x, y = c.pts(np.array([p]))[0]
    r = 3.8 * SS * s
    for dx, dy in ((-r * 0.9, -r), (r * 0.9, -r), (0, -r * 1.8), (0, -r * 0.9)):
        jitter = rng.uniform(-0.3, 0.3) * r
        box = [x + dx - r + jitter, y + dy - r, x + dx + r + jitter, y + dy + r]
        c.d.ellipse(box, fill=paper, outline=ink, width=max(1, SS // 2))


def cottonwood(c: Canvas, p, ink, paper) -> None:
    x, y = c.pts(np.array([p]))[0]
    """A broad crown of three lobes on a short trunk, taller than the oaks."""
    c.d.line([(x, y), (x, y - 5 * SS)], fill=ink, width=SS)
    r = 2.8 * SS
    for dx, dy in ((-r, -r * 0.9), (r, -r * 0.9), (0, -r * 1.9)):
        cx, cy = x + dx, y - 5 * SS + dy
        c.d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=paper, outline=ink, width=max(1, SS // 2))


def tuft(c: Canvas, p, ink) -> None:
    x, y = c.pts(np.array([p]))[0]
    for dx in (-1.6, 0, 1.6):
        c.d.line([(x + dx * SS, y), (x + dx * 1.6 * SS, y - 3 * SS)], fill=ink, width=max(1, SS // 2))


def shrub(c: Canvas, p, ink) -> None:
    x, y = c.pts(np.array([p]))[0]
    r = 1.1 * SS
    c.d.ellipse([x - r, y - 2 * r, x + r, y], outline=ink, width=max(1, SS // 2))


def upolu(v: View, rng: np.random.Generator, streams_flat: list) -> Canvas:
    """After the United States Exploring Expedition's Upolu (1839): fine, close hachures over the whole relief, and the
    land cover drawn in profile at an exaggerated size: here pine, oak, riparian trees, grass and scrub, with the
    towns as small blocks."""
    ink, paper = "#3a2e20", "#ebe1c6"
    c = Canvas(v, paper)
    f = v.f
    x, y = seeds(v.core, 44, rng)
    slope = f.at(f.slope, x, y)
    keep = (slope > 4) & (rng.random(x.size) < np.clip(slope / 25, 0.15, 1))
    x, y, slope = x[keep], y[keep], slope[keep]
    light = f.at(f.light, x, y)
    for i, run in visible_pieces(v, fall_lines(f, x, y, rng.uniform(110, 190, x.size))):
        c.line(run, 0.3 + 0.4 * (1 - light[i]), mix(ink, paper, 0.3 + 0.45 * (1 - light[i])))
    draw_kind(c, v, "stream", lambda p: 0.7 + (p["ord"] - 3) * 0.3, mix("#4b6676", paper, 0.85))
    draw_kind(c, v, "road", 0.6, mix(ink, paper, 0.7))
    draw_kind(c, v, "crest", 0.8, ink)
    # Land cover, drawn back to front so nearer symbols overlap farther ones.
    tree = cKDTree(np.concatenate([xy for _, xy in streams_flat])) if streams_flat else None
    x, y = seeds(v.core, 330, rng)
    z, slope, north = f.at(v.g.Z, x, y), f.at(f.slope, x, y), f.at(f.north, x, y)
    near_water = tree.query(np.column_stack([x, y]))[0] < RIPARIAN if tree else np.zeros(x.size, bool)
    lower = np.where(north > 0.5, NORTH_DROP, 0)
    kind = np.select(
        [near_water & (z < OAK), z >= PINE - lower, z >= OAK - lower, slope < 3, slope < 15],
        ["riparian", "pine", "oak", "grass", "scrub"],
        "",
    )
    density = {"riparian": 0.3, "pine": 0.7, "oak": 0.55, "grass": 0.35, "scrub": 0.4}
    marks = []
    for k, xx, yy in zip(kind, x, y, strict=True):
        if k and rng.random() < density[k]:
            for run in v.project(np.array([[xx, yy], [xx + 1, yy]])):
                marks.append((run[0][1], k, tuple(run[0])))
    for _, k, p in sorted(marks, key=lambda m: -m[0]):
        if k == "pine":
            pine(c, p, ink, paper, rng.uniform(0.8, 1.15))
        elif k == "oak":
            oak(c, p, ink, paper, rng, rng.uniform(0.8, 1.1))
        elif k == "riparian":
            cottonwood(c, p, ink, paper)
        elif k == "grass":
            tuft(c, p, mix(ink, paper, 0.75))
        else:
            shrub(c, p, mix(ink, paper, 0.8))

    def village(c: Canvas, p) -> None:
        for _ in range(7):
            q = (p[0] + rng.uniform(-260, 260), p[1] + rng.uniform(-160, 160))
            x0, y0 = c.pts(np.array([q]))[0]
            c.d.rectangle([x0, y0, x0 + 3 * SS, y0 + 1.6 * SS], fill=ink)

    label_places(c, v, ink, village)
    return c


# ---- Atlas combinations ---------------------------------------------------------------------------------------
# The Atlas of Oblique Maps strokes as the base, on the site's paper and ink, with parts of the other looks that stay
# plain lines and points: Guanabara's stipple on the flats, and from the comic look lit faces left blank, packed and
# heavier strokes in the deepest shade, heavier crests and rivers drawn as two banks.

PAPER, INK, WATER = "#f5edd3", "#2b2118", "#8fb3c4"


def atlas(
    v: View,
    rng: np.random.Generator,
    stipple: bool = False,
    comic: bool = False,
    paper: str = PAPER,
    ink: str = INK,
    c: "Canvas | None" = None,
) -> Canvas:
    c = c or Canvas(v, paper)
    f = v.f
    if stipple:
        x, y = seeds(v.core, 95, rng)
        flat = (f.at(f.slope, x, y) < 4) & (f.at(f.relief, x, y) < 40)
        for xy in np.column_stack([x[flat], y[flat]]):
            for run in v.project(np.array([xy, xy + [1, 0]])):
                c.dot(tuple(run[0]), 0.55, mix(ink, paper, 0.75))
    else:
        for row in np.arange(v.core[1], v.core[3], 110):
            xs = np.arange(v.core[0], v.core[2], 10.0)
            ys = np.full_like(xs, row + rng.uniform(-20, 20))
            flat = (f.at(f.slope, xs, ys) < 3.5) & (np.sin(xs / rng.uniform(35, 60) + rng.uniform(0, 6)) > -0.1)
            edges = np.flatnonzero(np.diff(np.concatenate([[0], flat.astype(np.int8), [0]])))
            for a, b in zip(edges[::2], edges[1::2], strict=True):
                if b - a >= 3:
                    for run in v.project(np.column_stack([xs[a:b], ys[a:b]])):
                        c.line(run, 0.5, mix(ink, paper, 0.7))
    x, y = seeds(v.core, 52, rng)
    slope, light = f.at(f.slope, x, y), f.at(f.light, x, y)
    keep = (slope > 5) & (
        rng.random(x.size) < np.clip(0.04 + 1.3 * (1 - light) ** 2.2, 0, 1) * np.clip(slope / 14, 0, 1)
    )
    if comic:
        keep &= light < 0.72
        # The deepest shade gets a second, offset set of seeds, so its strokes pack into near-solid masses.
        x2, y2 = seeds(v.core, 30, rng)
        deep = (f.at(f.slope, x2, y2) > 8) & (f.at(f.light, x2, y2) < 0.3)
        x, y = np.concatenate([x[keep], x2[deep]]), np.concatenate([y[keep], y2[deep]])
    else:
        x, y = x[keep], y[keep]
    light = f.at(f.light, x, y)
    strokes = fall_lines(f, x, y, rng.uniform(140, 320, x.size))
    for i, run in visible_pieces(v, strokes):
        dark = 1 - light[i]
        width = 0.3 + 0.8 * dark + (0.9 * max(0, 0.3 - light[i]) / 0.3 if comic else 0)
        c.line(run, width, ink)
    if comic:
        draw_kind(c, v, "stream", lambda p: 2.4 + (p["ord"] - 3) * 0.6, ink)
        draw_kind(c, v, "stream", lambda p: 1.2 + (p["ord"] - 3) * 0.6, WATER)
    else:
        draw_kind(c, v, "stream", lambda p: 0.7 + (p["ord"] - 3) * 0.25, "#3f6f8a")
    draw_kind(c, v, "road", 0.6, ink)
    border(c, v, ink)
    draw_kind(c, v, "crest", 1.7 if comic else 1.2, ink)
    label_places(c, v, ink)
    return c


def border(c: Canvas, v: View, ink) -> None:
    """The international line, dash and dot."""
    for _, xy in v.lines.get("country", []):
        d = np.concatenate([[0], np.cumsum(np.hypot(*np.diff(xy, axis=0).T))])
        on = (d % 600) < 380
        edges = np.flatnonzero(np.diff(np.concatenate([[0], on.astype(np.int8), [0]])))
        for a, b in zip(edges[::2], edges[1::2], strict=True):
            if b - a >= 2:
                c.line(xy[a:b], 1.3, ink)


# ---- Land cover -----------------------------------------------------------------------------------------------
# INEGI's 1:250,000 land use and vegetation (from SEMARNAT's Atlas 2022 service, which republishes it; the service
# does not name the series) in Mexico, and NLCD 2021 (MRLC) in the US, both folded into one legend. The colours are
# flat tints after the classic school-atlas palette: greens for trees, straw for grass, adobe for scrub.
LANDCOVER = CACHE / "landcover"
LEGEND = {  # class: (tint, the INEGI CLAVE values, the NLCD codes)
    "water": ("#9cc3d3", {"H2O"}, {11}),
    "riparian": ("#7fae63", {"BG", "VG"}, {90, 95}),
    "pine": ("#86a26c", {"BP", "BPQ"}, set()),
    "oak": ("#b3bf80", {"BQ", "BQP", "VSA/BQ", "VSa/BQ", "VSa/BQP", "VSa/BPQ"}, {41, 42, 43}),
    "grass": ("#ecdc98", {"PN", "PI", "PC", "VSa/PN"}, {71}),
    "scrub": ("#e3c39b", {"MDM", "MDR", "MK", "ML"}, {52, 31}),
    "fields": ("#c9d27c", {"RA", "RAS"}, {81, 82}),
    "town": ("#d4876a", {"AH"}, {21, 22, 23, 24}),
}
CLASSES = list(LEGEND)
SIEVE = 40  # cells (3.6 ha)


def landcover_grid(v: View):
    """The view's DEM grid as a north-up raster: its shape and transform."""
    ny, nx = v.g.Z.shape
    return (ny, nx), rasterio.transform.from_origin(v.g.x0, v.g.y0 + ny * CELL, CELL, CELL)


def warped(path: Path, v: View) -> np.ndarray:
    """A categorical raster resampled (nearest) onto the view's grid, north-up."""
    from rasterio.enums import Resampling
    from rasterio.warp import reproject

    shape, transform = landcover_grid(v)
    out = np.zeros(shape, dtype=np.uint8)
    with rasterio.open(path) as src:
        reproject(
            rasterio.band(src, 1),
            out,
            src_transform=src.transform,
            src_crs=src.crs,
            dst_transform=transform,
            dst_crs=po.CRS,
            resampling=Resampling.nearest,
        )
    return out


def sieved(out: np.ndarray) -> np.ndarray:
    """Patches under SIEVE cells join their neighbours, so 30 m pixels read as drawn edges; flipped south to north
    like the Grid."""
    from rasterio.features import sieve

    return (sieve((out + 1).astype(np.int32), size=SIEVE) - 1)[::-1].astype(np.int16)


def landcover(v: View, box: str) -> np.ndarray:
    """INEGI over NLCD: each DEM cell's class (an index into CLASSES, or -1), south to north like the Grid."""
    from rasterio.features import rasterize
    from shapely.geometry import shape as to_shape

    shape, transform = landcover_grid(v)
    out = np.full(shape, -1, dtype=np.int16)
    nlcd_path = LANDCOVER / "nlcd" / f"{box}.tif"
    if nlcd_path.exists():
        codes = warped(nlcd_path, v)
        for k, (_, _, nlcd) in enumerate(LEGEND.values()):
            out[np.isin(codes, list(nlcd))] = k
    shapes = []
    for feat in json.loads((LANDCOVER / "inegi-s7" / f"{box}.geojson").read_text())["features"]:
        key = feat["properties"]["CLAVE"]
        k = next((i for i, (_, inegi, _) in enumerate(LEGEND.values()) if key in inegi), -1)
        if k >= 0:
            geom = shapely.transform(to_shape(feat["geometry"]), lambda xy: np.column_stack(po.to_utm(*xy.T)))
            shapes.append((geom, k))
    inegi = rasterize(shapes, out_shape=shape, transform=transform, fill=-1, dtype="int16")
    return sieved(np.where(inegi >= 0, inegi, out))


# The CEC's North American Land Cover 2020 (30 m, v2; fetch_cec.py): one classification across Mexico and the US,
# so it has no seam at the border. Its 19 classes are continental, so its forests are not split into pine and oak.
CEC_TREES = {1, 2, 3, 4, 5, 6}  # needleleaf, broadleaf evergreen and deciduous, and mixed forest
CEC_SHRUB = {7, 8, 11, 13, 16}  # shrubland, and the barren classes
CEC_GRASS = {9, 10, 12}
WOODLAND_SLOPE = 6  # degrees, on the smoothed DEM
CEC_PLAIN = {  # class: CEC codes, read without the height
    "water": {18},
    "riparian": {14},
    "pine": {1, 2, 6},
    "oak": {3, 4, 5},
    "grass": CEC_GRASS,
    "scrub": CEC_SHRUB,
    "fields": {15},
    "town": {17},
}


def cec_codes(v: View) -> np.ndarray:
    """The CEC classes on the view's grid, north-up; Mexico's file first, then the US's where Mexico's has none."""
    out = np.zeros(landcover_grid(v)[0], dtype=np.uint8)
    for country in ("mex", "usa"):
        codes = warped(LANDCOVER / "cec" / f"{country}.tif", v)
        out = np.where((out == 0) & (codes > 0) & (codes < 20), codes, out)
    return out


def landcover_cec(v: View) -> np.ndarray:
    """The CEC classes in the lab's legend, south to north like the Grid."""
    codes = cec_codes(v)
    out = np.full(codes.shape, -1, dtype=np.int16)
    for k, name in enumerate(CLASSES):
        out[np.isin(codes, list(CEC_PLAIN[name]))] = k
    return sieved(out)


def landcover_brown(v: View, streams: list) -> np.ndarray:
    """The CEC map read with Brown's bands (OAK, PINE, NORTH_DROP, RIPARIAN above). The CEC decides what height
    cannot: water, towns, fields, wetland, and grass against scrub in the valleys. Height decides what the CEC
    cannot: which trees. Trees below the oak line are gallery forest; above it oak, and above the pine line pine.
    Shrubland above the oak line and on a slope of WOODLAND_SLOPE or more is open Madrean woodland, so oak: the
    woodland climbs the mountains, while basin floors as high as the oak line (the Animas and San Luis valleys, at
    1,300 to 1,600 m) stay grassland and scrub. Within RIPARIAN m of a stream of order 4 or more, below the oak
    line, trees and scrub are gallery forest."""
    from rasterio.features import rasterize
    from scipy.ndimage import distance_transform_edt

    codes = cec_codes(v)
    shape, transform = landcover_grid(v)
    z = v.g.Z[::-1]
    # North slopes count as higher: up to NORTH_DROP m on a slope facing due north.
    height = z + NORTH_DROP * np.clip(v.f.north[::-1], 0, 1)
    band = np.select([height >= PINE, height >= OAK], [2, 1], 0)
    slope = v.f.slope[::-1] >= WOODLAND_SLOPE
    lines = [shapely.LineString(xy) for _, xy in streams if len(xy) > 1]
    on_stream = rasterize(lines, out_shape=shape, transform=transform, all_touched=True) > 0 if lines else None
    near = (distance_transform_edt(~on_stream) * CELL < RIPARIAN) if lines else np.zeros(shape, bool)
    trees, shrub, grass = (
        np.isin(codes, list(CEC_TREES)),
        np.isin(codes, list(CEC_SHRUB)),
        np.isin(codes, list(CEC_GRASS)),
    )
    k = CLASSES.index
    out = np.select(
        [
            codes == 18,
            codes == 17,
            codes == 15,
            codes == 14,
            (trees | shrub) & near & (band == 0),
            trees & (band == 0),
            trees & (band == 2),
            trees & (band >= 1),
            shrub & (band >= 1) & slope,
            shrub,
            grass,
        ],
        [
            k("water"),
            k("town"),
            k("fields"),
            k("riparian"),
            k("riparian"),
            k("riparian"),
            k("pine"),
            k("oak"),
            k("oak"),
            k("scrub"),
            k("grass"),
        ],
        -1,
    ).astype(np.int16)
    return sieved(out)


def tinted(v: View, classes: np.ndarray, paper: str, cartoon: bool) -> np.ndarray:
    """The land cover seen from the view, as output pixels. Classic: flat tints. Cartoon: each tint in two tones,
    darker on the faces turned from the light, with every class edge drawn in its own darker tone."""
    rows, cols = v.surface()
    seen = rows >= 0
    cls = np.where(seen, classes[np.maximum(rows, 0), cols[None, :]], -1)
    light = np.where(seen, v.f.light[np.maximum(rows, 0), cols[None, :]], 1)
    out = np.empty(cls.shape + (3,), dtype=float)
    out[:] = rgb(paper)
    for k, (tint, _, _) in enumerate(LEGEND.values()):
        colour = np.array(mix(tint, paper, 0.75 if cartoon else 0.6), dtype=float)
        m = cls == k
        if cartoon:
            out[m] = colour
            out[m & (light < 0.5)] = colour * 0.82
        else:
            out[m] = colour
    if cartoon:
        edge = np.zeros(cls.shape, bool)
        edge[:, 1:] |= cls[:, 1:] != cls[:, :-1]
        edge[1:, :] |= cls[1:, :] != cls[:-1, :]
        edge &= cls >= 0
        out[edge] = out[edge] * 0.62
    return out


def atlas_landcover(v: View, rng: np.random.Generator, classes: np.ndarray, cartoon: bool) -> Canvas:
    c = Canvas(v, PAPER)
    c.underlay(tinted(v, classes, PAPER, cartoon))
    return atlas(v, rng, stipple=True, comic=True, c=c)


# ---- Main -----------------------------------------------------------------------------------------------------

LOOKS = [
    "current",
    "steeper-toned",
    "alpha",
    "guanabara",
    "trentino",
    "comic",
    "upolu",
    "atlas-paper",
    "atlas-stipple",
    "atlas-comic",
    "atlas-stipple-comic",
    "atlas-landcover",
    "atlas-landcover-cartoon",
    "cec",
    "cec-cartoon",
    "cec-brown",
    "cec-brown-cartoon",
]
BORDER_LOOKS = [
    "border-current",
    "border-atlas-stipple-comic",
    "border-atlas-landcover",
    "border-atlas-landcover-cartoon",
    "border-cec",
    "border-cec-cartoon",
    "border-cec-brown",
    "border-cec-brown-cartoon",
]


class Scene:
    """One box: its DEM, lowest ground, base lines, and a View for each lean, made when first asked for."""

    def __init__(self, name: str):
        self.name, self.box = name, BOXES[name]
        box, pad = self.box, po.PAD
        self.bounds = (box[0] - pad, box[1] - SOUTH, box[2] + pad, box[3] + pad)
        self.path = dem(f"dem-{name}", self.bounds)
        with rasterio.open(self.path) as src:
            window = from_bounds(*box, transform=src.transform).round_offsets().round_lengths()
            self.base = float(src.read(1, window=window).min())
        print(f"{name}: lowest ground {self.base:.0f} m", flush=True)
        west, south = po.to_wgs(self.bounds[0], self.bounds[1])
        east, north = po.to_wgs(self.bounds[2], self.bounds[3])
        with tempfile.TemporaryDirectory() as tmp:
            self.lines, self.mexico = po.base_lines((west - 0.05, south - 0.05, east + 0.05, north + 0.05), Path(tmp))
        self.streams = [(p, xy) for k, p, xy in self.lines if k == "stream" and p.get("ord", 0) >= 4]
        self.views: dict[float, View] = {}

    def view(self, lean: float) -> View:
        if lean not in self.views:
            wide = (self.box[0], self.box[1] - SOUTH, self.box[2], self.box[3])
            self.views[lean] = View(
                f"{self.name}-lean{lean}", self.path, self.base, lean, wide, self.box, self.lines, self.mexico
            )
        return self.views[lean]

    def block(self, lean: float) -> View:
        box = self.box
        relief = gaussian_filter(rasterio.open(self.path).read(1), 1).max() - self.base
        win = (box[0], box[1] - WALL * lean - 600, box[2], box[3] + relief * lean * 0.85)
        return View(
            f"{self.name}-block{lean}",
            crop_south(self.path, box[1]),
            self.base,
            lean,
            box,
            win,
            self.lines,
            self.mexico,
        )


def render(look: str, s: Scene) -> Canvas:
    rng = np.random.default_rng(7)
    look = look.removeprefix("border-")
    match look:
        case "current":
            return current(s.view(2))
        case "steeper-toned":
            return steeper_toned(s.view(4))
        case "alpha":
            return alpha(s.view(4), rng)
        case "guanabara":
            return guanabara(s.view(4), rng)
        case "comic":
            return comic(s.view(4), rng)
        case "upolu":
            return upolu(s.view(3), rng, s.streams)
        case "trentino":
            return trentino(s.block(3), rng)
        case "atlas-paper":
            return atlas(s.view(4), rng)
        case "atlas-stipple":
            return atlas(s.view(4), rng, stipple=True)
        case "atlas-comic":
            return atlas(s.view(4), rng, comic=True)
        case "atlas-stipple-comic":
            return atlas(s.view(4), rng, stipple=True, comic=True)
        case "atlas-landcover" | "atlas-landcover-cartoon":
            v = s.view(4)
            return atlas_landcover(v, rng, landcover(v, s.name), cartoon=look.endswith("cartoon"))
        case "cec" | "cec-cartoon":
            v = s.view(4)
            return atlas_landcover(v, rng, landcover_cec(v), cartoon=look.endswith("cartoon"))
        case "cec-brown" | "cec-brown-cartoon":
            v = s.view(4)
            return atlas_landcover(v, rng, landcover_brown(v, s.streams), cartoon=look.endswith("cartoon"))
    sys.exit(f"unknown look {look}; choose from {', '.join(LOOKS + BORDER_LOOKS)}")


def main(only: list[str]) -> None:
    scenes: dict[str, Scene] = {}
    for name in only or LOOKS + BORDER_LOOKS:
        box = "border" if name.startswith("border-") else "pilares"
        if box not in scenes:
            scenes[box] = Scene(box)
        print(f"wrote {render(name, scenes[box]).save(name).relative_to(ROOT)}", flush=True)


if __name__ == "__main__":
    main(sys.argv[1:])
