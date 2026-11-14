"""Landform axes for the Wheeler lab demo: a label line along each named range, mesa, valley and plain.

Run from the repo root: uv run --project pipeline python review/stage-8/wheeler/landform_axes.py
Writes site/src/lab/wheeler/landforms.ts (a GeoJSON FeatureCollection as a TypeScript module).

The gazetteers give most landforms as a single point (GNIS Range, Ridge, Summit, Flat; GeoNames MTS, MESA, PLN),
so the axis comes from the DEM around the point:
  1. Read a window of the Copernicus GLO-30 mosaic around the point (RADIUS_KM by kind), resampled to CELL_M.
  2. Ranges: keep the cells whose height above the local valley floor (the lowest ground within VALLEY_KM,
     smoothed) is more than SHARE of that height near the point, so a range is cut off from a higher neighbour by
     the valley between. Mesas: keep the flat cells (under FLAT_DEG) within MESA_DROP_M of the top near the point.
     Plains: the flat cells lower than base + SHARE * (top - base), base the window's 20th percentile.
  3. Of those cells, keep the connected region that contains (or lies nearest to) the gazetteer point.
  4. The principal axis of that region (PCA of the cell positions in metres, weighted by height) gives the label's direction; the
     label line runs through the region's centroid, AXIS_SPAN standard deviations each way along the major axis.
GNIS valleys also carry a source point (the head) beside the primary point (the mouth); for those the axis is
simply the line from one to the other, which is what a cartographer would set the name along.
Named mesas come from data/mountain_glyphs.geojson; only the long, elongated flat tops are kept.

Every feature keeps its source and licence: GNIS is public domain; GeoNames is CC BY 4.0.
"""

import csv
import json
import math
from pathlib import Path

import numpy as np
import rasterio
from rasterio.enums import Resampling
from rasterio.windows import from_bounds
from scipy import ndimage

REPO = Path(__file__).resolve().parents[3]
PRIVATE = Path('/Users/jb/repos/crossing-map/private') if not (REPO / 'private').exists() else REPO / 'private'
DEM = PRIVATE / 'cache' / 'least-cost' / 'dem.vrt'
GAZ = PRIVATE / 'cache' / 'gazetteer'
OUT = REPO / 'site' / 'src' / 'lab' / 'wheeler' / 'landforms.ts'
CELL_M = {'range': 150, 'mesa': 90, 'plain': 150}
RADIUS_KM = {'range': 30, 'mesa': 12, 'plain': 30}
SHARE = {'range': 0.25, 'mesa': 0.85, 'plain': 0.25}
# Mesa tops and plains: slope below this many degrees.
FLAT_DEG = {'mesa': 8, 'plain': 2}
# The landform's own top: the highest ground this close to the point (km), so a higher range nearby does not set it.
# Mesas: the top is the ground no more than this far below the highest point near the gazetteer point (m).
MESA_DROP_M = 80
# Ranges: the valley floor is the lowest ground within this distance (km).
VALLEY_KM = 8
NEAR_KM = {'range': 6, 'mesa': 1.5, 'plain': 30}
AXIS_SPAN = 1.8

# (name as in the gazetteer, source, gazetteer class or code, kind on the map)
WANTED = [
    ('Animas Mountains', 'gnis', 'Range', 'range'),
    ('Peloncillo Mountains', 'gnis', 'Range', 'range'),
    ('Big Hatchet Mountains', 'gnis', 'Range', 'range'),
    ('Little Hatchet Mountains', 'gnis', 'Range', 'range'),
    ('Pyramid Mountains', 'gnis', 'Range', 'range'),
    ('Chiricahua Mountains', 'gnis', 'Range', 'range'),
    ('Florida Mountains', 'gnis', 'Range', 'range'),
    ('Animas Valley', 'gnis', 'Valley', 'valley'),
    ('Playas Valley', 'gnis', 'Valley', 'valley'),
    ('Hachita Valley', 'gnis', 'Valley', 'valley'),
    ('San Simon Valley', 'gnis', 'Valley', 'valley'),
    ('San Bernardino Valley', 'gnis', 'Valley', 'valley'),
    ('Sierra el Tigre', 'geonames', 'MTS', 'range'),
    ('Sierra San Luis', 'geonames', 'MTS', 'range'),
    ('Sierra Huachinera', 'geonames', 'MTS', 'range'),
    ('Sierra Carcay', 'geonames', 'MTS', 'range'),
    ('Serranía Pilares de Teras', 'geonames', 'MTS', 'range'),
    ('Sierra el Nido', 'geonames', 'MTS', 'range'),
    ('Llanos de Carretas', 'geonames', 'PLN', 'plain'),
]
BOX = (-112, 28, -104, 34)


def gnis():
    out = {}
    for f in GAZ.glob('DomesticNames_*_Text/Text/*.txt'):
        with open(f, encoding='utf-8-sig') as fh:
            for r in csv.DictReader(fh, delimiter='|'):
                lat, lon = float(r['prim_lat_dec'] or 0), float(r['prim_long_dec'] or 0)
                if not (BOX[0] <= lon <= BOX[2] and BOX[1] <= lat <= BOX[3]):
                    continue
                src = (float(r['source_long_dec'] or 0), float(r['source_lat_dec'] or 0))
                out.setdefault((r['feature_name'], r['feature_class']), (lon, lat, src if src[0] else None, r['feature_id']))
    return out


def geonames():
    out = {}
    with open(GAZ / 'MX' / 'MX.txt', encoding='utf-8') as fh:
        for r in csv.reader(fh, delimiter='\t'):
            lat, lon = float(r[4]), float(r[5])
            if BOX[0] <= lon <= BOX[2] and BOX[1] <= lat <= BOX[3]:
                out.setdefault((r[1], r[7]), (lon, lat, None, r[0]))
    return out


def axis(dem, lon, lat, kind):
    """The label line (two lon/lat points) and the region's length in metres, from the DEM around a point."""
    r = RADIUS_KM[kind] * 1000
    kx = 111320 * math.cos(math.radians(lat))
    dlon, dlat = r / kx, r / 110540
    win = from_bounds(lon - dlon, lat - dlat, lon + dlon, lat + dlat, dem.transform)
    cell = CELL_M[kind]
    n = int(2 * r / cell)
    z = dem.read(1, window=win, out_shape=(n, n), resampling=Resampling.average).astype(float)
    c = n // 2
    near = int(NEAR_KM[kind] * 1000 / cell)
    base = np.percentile(z, 20)
    top = np.percentile(z[max(c - near, 0):c + near, max(c - near, 0):c + near], 99)
    gy, gx = np.gradient(z, cell)
    slope = np.degrees(np.arctan(np.hypot(gx, gy)))
    if kind == 'plain':
        mask = z < base + SHARE[kind] * (top - base)
    elif kind == 'range':
        # Height above the local valley floor (the lowest ground within VALLEY_KM, smoothed), so a range is cut off
        # from its neighbour by the valley between them even when the neighbour is higher.
        k = int(VALLEY_KM * 1000 / cell) | 1
        floor = ndimage.uniform_filter(ndimage.minimum_filter(z, size=k), size=k)
        rel = z - floor
        rel_top = np.percentile(rel[max(c - near, 0):c + near, max(c - near, 0):c + near], 99)
        mask = rel > SHARE[kind] * rel_top
        base = 0
        z = rel
    else:
        # A mesa top: the flat ground within MESA_DROP_M (or a share of the relief, if larger) of the top near the point.
        mask = z > top - max(MESA_DROP_M, (1 - SHARE[kind]) * (top - base))
    if kind in FLAT_DEG:
        mask &= slope < FLAT_DEG[kind]
    mask = ndimage.binary_fill_holes(ndimage.binary_opening(mask, iterations=1))
    lab, count = ndimage.label(mask)
    if not count:
        return None
    if lab[c, c]:
        keep = lab[c, c]
    else:
        # The nearest region to the point: gazetteer points sit on a summit or in the middle of a name, not always
        # inside the region the thresholds find.
        d, (iy, ix) = ndimage.distance_transform_edt(lab == 0, return_indices=True)
        keep = lab[iy[c, c], ix[c, c]]
    ys, xs = np.nonzero(lab == keep)
    if len(xs) < 8:
        return None
    # Cell positions in metres east and north of the window centre.
    px = (xs - c) * cell
    py = (c - ys) * cell
    # Weighted by height above the base, so the crest counts for more than the foothills.
    w = np.clip(z[ys, xs] - base, 1, None) if kind != 'plain' else np.ones(len(xs))
    cx, cy = np.average(px, weights=w), np.average(py, weights=w)
    cov = np.cov(np.vstack([px - cx, py - cy]), aweights=w)
    ev, vec = np.linalg.eigh(cov)
    major = vec[:, 1]
    half = AXIS_SPAN * math.sqrt(ev[1])
    # Read left to right, as map lettering is.
    if major[0] < 0:
        major = -major
    pts = [(cx - major[0] * half, cy - major[1] * half), (cx + major[0] * half, cy + major[1] * half)]
    line = [[round(lon + x / kx, 5), round(lat + y / 110540, 5)] for x, y in pts]
    elong = math.sqrt(ev[1] / max(ev[0], 1))
    return line, 2 * half, elong


# Named mesas from data/mountain_glyphs.geojson (crossing.peaks and crossing.landforms) are tried as well; only those
# whose flat top is at least MESA_MIN_KM long and clearly elongated are kept, as only those suit a label along an axis.
MESA_MIN_KM = 2.5
MESA_MIN_ELONG = 1.6


def glyph_mesas():
    glyphs = json.loads((REPO / 'data' / 'mountain_glyphs.geojson').read_text())['features']
    for f in glyphs:
        p = f['properties']
        if p['landform'] == 'mesa' and not p['name'].startswith('Unnamed'):
            lon, lat = f['geometry']['coordinates']
            source = 'gnis' if (p.get('name_code') or '').startswith('gnis') else 'geonames'
            yield p['name'], source, (lon, lat, None, p.get('source_id') or p['id'])


def main():
    g, m = gnis(), geonames()
    feats = []
    wanted = [(n, s, c, k, None) for n, s, c, k in WANTED]
    wanted += [(n, s, 'MESA', 'mesa', hit) for n, s, hit in glyph_mesas()]
    with rasterio.open(DEM) as dem:
        for name, source, code, kind, hit in wanted:
            hit = hit or (g if source == 'gnis' else m).get((name, code))
            if not hit:
                print('not found:', name, code)
                continue
            lon, lat, src, fid = hit
            if kind == 'valley':
                if not src:
                    print('no source point:', name)
                    continue
                a, b = sorted([[round(lon, 5), round(lat, 5)], [round(src[0], 5), round(src[1], 5)]])
                kx = 111320 * math.cos(math.radians(lat))
                length = math.hypot((b[0] - a[0]) * kx, (b[1] - a[1]) * 110540)
                line, method, elong = [a, b], 'GNIS primary (mouth) and source (head) points', None
            else:
                res = axis(dem, lon, lat, kind)
                if not res:
                    print('no region:', name)
                    continue
                line, length, elong = res
                if kind == 'mesa' and (length < MESA_MIN_KM * 1000 or elong < MESA_MIN_ELONG):
                    continue
                method = 'principal axis of the DEM region around the gazetteer point'
            props = {
                'name': name, 'kind': kind, 'len_m': round(length), 'mpp0': round(156543.03 * math.cos(math.radians(lat))),
                'source': f'{"USGS GNIS" if source == "gnis" else "GeoNames"} {fid}',
                'licence': 'public domain' if source == 'gnis' else 'CC BY 4.0', 'method': method,
            }
            if elong:
                props['elongation'] = round(elong, 2)
            feats.append({'type': 'Feature', 'geometry': {'type': 'LineString', 'coordinates': line}, 'properties': props})
            print(f'{name:28s} {kind:6s} {length / 1000:6.1f} km  elong {elong or 0:.1f}')
    body = json.dumps({'type': 'FeatureCollection', 'features': feats}, ensure_ascii=False, indent=1)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(
        '// Generated by review/stage-8/wheeler/landform_axes.py: a label line along each demo landform, from GNIS\n'
        '// (public domain) and GeoNames (CC BY 4.0) names, the axis from the gazetteer or the Copernicus DEM.\n'
        "import type { FeatureCollection, LineString } from 'geojson'\n\n"
        'export type LandformProps = { name: string; kind: string; len_m: number; mpp0: number; source: string; licence: string; '
        'method: string; elongation?: number }\n\n'
        f'export const landforms: FeatureCollection<LineString, LandformProps> = {body}\n'
    )


if __name__ == '__main__':
    main()
