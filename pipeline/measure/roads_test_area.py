"""Historic roads of the Wheeler test area, traced by hand, written as a seed.

Run from the repo root: uv run --project pipeline python pipeline/measure/roads_test_area.py

Writes pipeline/seeds/roads/test-area.geojson and the lab's copy,
site/public/lab/wheeler/roads-test-area.geojson, and prints the length of
each traced road and of the stretches the book gives a distance for.

Sources (both public domain, USGS Historical Topographic Map Collection,
cached in private/cache/roads/usgs-htmc/, never committed):
- Cienega Springs, N. Mex., 1:62,500, edition of 1918 (surveyed 1917-18),
  scan 189304.
- Animas Peak, N. Mex., 1:62,500, 1918 (1963 reprint), scan 189578.

Method: each sheet was cropped with gdal_translate, the crops were looked at,
and road vertices were picked by eye in full-resolution pixel coordinates
(column, row). Solid double lines on the sheets are roads (class
wagon-road), dashed double lines poorer roads and trails (class trail). A
pixel centre is converted with the GeoTIFF's geotransform to the sheets'
CRS, American Polyconic on NAD27 (lon_0 -108.875, lat_0 0, metres), then
to WGS 84 with pyproj. NADCON grids are not installed, so pyproj uses the
CONUS Helmert shift NAD27 to WGS 84 (EPSG:1173, about 10 m). The sheets
themselves predate NAD27 (the reprint's note says to move the projection
lines 100 feet west for NAD27), and a picked vertex is good to about 2 pixels
(11 m), so a vertex is good to about 40 m: under the width of the line at
1:62,500.

The NPS Butterfield Overland National Historic Trail (public domain, US
federal work) is clipped from the cached feature-service answer to the test
area widened north to 32.4 deg N, because the trail runs through Stein's Pass
and Lordsburg, north of the test area.

Lengths are geodesic on the WGS 84 ellipsoid (pyproj.Geod).
"""

import json
import math
from pathlib import Path

from pyproj import Geod, Transformer
from shapely.geometry import LineString, Point, box, mapping, shape
from shapely.ops import linemerge, substring, unary_union

ROOT = Path(__file__).resolve().parents[2]
SEED = ROOT / 'pipeline/seeds/roads/test-area.geojson'
LAB = ROOT / 'site/public/lab/wheeler/roads-test-area.geojson'
BUTTERFIELD = ROOT / 'private/cache/roads/nps/buov-box-109.6-30.5-108.4-32.4.geojson'

# The test area (brief of 14 November 2026), widened north to 32.4 deg N for the Butterfield trail only.
BUTTERFIELD_BOX = box(-109.6, 30.5, -108.4, 32.4)

GEOD = Geod(ellps='WGS84')
TO_WGS84 = Transformer.from_pipeline(
    '+proj=pipeline +step +inv +proj=poly +lat_0=0 +lon_0=-108.875 +x_0=0 +y_0=0 +ellps=clrk66 '
    '+step +proj=cart +ellps=clrk66 +step +proj=helmert +x=-8 +y=160 +z=176 '
    '+step +inv +proj=cart +ellps=WGS84'
)

# Geotransforms read with gdalinfo from the cached GeoTIFFs: origin x, pixel width, origin y, pixel height (metres).
SHEETS = {
    'cienega': {
        'transform': (-13498.998452659739996, 5.291666666666667, 3488111.758673366159201, -5.291666666666615),
        'source': 'USGS Cienega Springs, N. Mex., 1:62,500, 1918',
    },
    'animas': {
        'transform': (-13351.884107743673667, 5.291666666666666, 3516409.404528701212257, -5.291666666666667),
        'source': 'USGS Animas Peak, N. Mex., 1:62,500, 1918 (1963 reprint)',
    },
}
LICENCE = 'Public domain (USGS). Credit: U.S. Geological Survey, Historical Topographic Map Collection.'

# Points the book's distances are measured between (data/stops.geojson): the Parham house is placed at
# Cloverdale, and the SK Bar is Sanders' ranch.
CLOVERDALE = (-108.92977, 31.41705)
SK_BAR = (-108.9, 31.545)

# Each road: its parts in drawing order, as (sheet, [(column, row), ...]) in full-resolution pixels.
ROADS = [
    {
        'id': 'road-cloverdale-san-luis-pass',
        'class': 'wagon-road',
        'certainty': 'traced',
        'first_seen': '1-03',
        'book_name': 'road to Fitzpatrick Wells',
        'note': 'East from Cloverdale past Fitzpatricks Well to San Luis Pass, the main road across the valley. '
                'The brothers cross it on their way into the Peloncillos.',
        'parts': [('cienega', [(1530, 2105), (1800, 2102), (2030, 2105), (2100, 2135), (2240, 2156), (2380, 2190),
                               (2460, 2250), (2524, 2310), (2660, 2330), (2770, 2378), (2900, 2410), (3060, 2444),
                               (3300, 2456), (3520, 2480), (3720, 2510), (3880, 2524), (4060, 2512), (4120, 2530),
                               (4240, 2550), (4400, 2576), (4470, 2550), (4600, 2516), (4720, 2510), (4790, 2522)])],
    },
    {
        'id': 'road-cloverdale-creek',
        'class': 'trail',
        'certainty': 'traced',
        'first_seen': '1-04',
        'book_name': 'Cloverdale Creek road',
        'mileage': '4 m.',
        'mileage_ref': '1-05',
        'note': 'Up Cloverdale Creek from Cloverdale into the Peloncillos, a dashed road on the sheet. Billy runs '
                'his trapline down to it. The book gives four miles from a spring by the road into Cloverdale; '
                "the spring's place on the road is not known, so the label marks the road, not the stretch.",
        'parts': [('cienega', [(1530, 2105), (1450, 2075), (1360, 2065), (1260, 2030), (1195, 1970), (1180, 1900),
                               (1155, 1860), (1120, 1830), (1060, 1800), (970, 1760), (900, 1732), (810, 1700),
                               (740, 1650), (690, 1595), (680, 1540), (675, 1445), (580, 1415), (440, 1368),
                               (305, 1390)])],
    },
    {
        'id': 'road-animas-valley',
        'class': 'wagon-road',
        'certainty': 'traced',
        'first_seen': '1-07',
        'book_name': 'road to Animas',
        'mileage': '9 m.',
        'mileage_ref': '1-02',
        'note': 'North from Cloverdale up the Animas Valley past the Gray Ranch and Gray School, the road to '
                'Animas. The book gives nine miles from the Parham place to the SK Bar; the label sits on that '
                'stretch.',
        'parts': [
            ('cienega', [(1730, 2100), (1760, 2050), (1820, 1990), (1910, 1890), (1995, 1800), (2078, 1575),
                         (2115, 1440), (2153, 1163), (2205, 1050), (2280, 900), (2340, 750), (2438, 563),
                         (2490, 488), (2535, 428), (2603, 357)]),
            ('animas', [(2580, 5703), (2620, 5650), (2640, 5570), (2625, 5470), (2590, 5420), (2560, 5350),
                        (2556, 5220), (2556, 5075),
                        (2538, 4900), (2519, 4713), (2506, 4563), (2523, 4478), (2525, 4275), (2538, 4175)]),
        ],
    },
    {
        'id': 'road-guadalupe-pass',
        'class': 'wagon-road',
        'certainty': 'traced',
        'first_seen': '2-04',
        'book_name': 'old road from Douglas',
        'note': 'From the Arizona line over Guadalupe Pass, down to a junction by the border and north to the '
                'crossing at bench mark 5231: the old road from Douglas to Cloverdale. West of the sheet it runs on '
                'down Guadalupe Canyon (McDonald, Ariz., 1922, not traced).',
        'parts': [('cienega', [(300, 3500), (365, 3582), (450, 3540), (540, 3488), (595, 3545), (600, 3600),
                               (600, 3660), (635, 3715), (700, 3690), (785, 3668), (825, 3615), (905, 3622),
                               (950, 3700), (1030, 3758), (1110, 3730), (1180, 3650), (1215, 3580), (1240, 3490),
                               (1250, 3375), (1310, 3260), (1430, 3180), (1610, 3110), (1690, 3070), (1740, 2950),
                               (1746, 2798)])],
    },
    {
        'id': 'road-guadalupe-cloverdale',
        'class': 'trail',
        'certainty': 'approximate',
        'first_seen': '2-04',
        'book_name': None,
        'note': 'The last stretch of the Douglas road into Cloverdale, a dashed road east of the hill in sections '
                '25 and 36. Where it joins the Cloverdale road is not clear on the scan.',
        'parts': [('cienega', [(1746, 2798), (1755, 2650), (1770, 2570), (1800, 2510), (1815, 2450), (1800, 2380),
                               (1765, 2345), (1755, 2250), (1750, 2105)])],
    },
    {
        'id': 'road-garcia',
        'class': 'wagon-road',
        'certainty': 'traced',
        'first_seen': '1-01',
        'book_name': None,
        'note': 'From the Peloncillo foothills south-east across the valley to bench mark 5175 by Fitzpatricks '
                'Well, then south to Garcia and the boundary at monument 67. The north part is dashed on the sheet.',
        'parts': [('cienega', [(1695, 525), (1740, 675), (1845, 945), (1950, 1140), (2055, 1283), (2145, 1410),
                               (2240, 1600), (2360, 1780), (2440, 1960), (2530, 2170), (2524, 2310), (2510, 2600),
                               (2505, 2975), (2538, 3080), (2587, 3380), (2658, 3385), (2695, 3710), (2758, 3842)])],
    },
    {
        'id': 'road-lang-ranch',
        'class': 'wagon-road',
        'certainty': 'traced',
        'first_seen': '1-01',
        'book_name': None,
        'note': 'South from below San Luis Pass to the Lang Ranch at Cienega Springs, then west along the '
                'boundary to Bramlett.',
        'parts': [('cienega', [(4400, 2576), (4200, 2660), (4080, 2740), (4000, 2860), (3955, 3020), (3895, 3200),
                               (3850, 3380), (3745, 3635), (3685, 3800), (3475, 3818), (3265, 3785), (3100, 3838)])],
    },
    {
        'id': 'road-skeleton-canyon',
        'class': 'trail',
        'certainty': 'traced',
        'first_seen': '1-01',
        'book_name': None,
        'note': 'Down Skeleton Canyon out of the Peloncillos to the Cowan Ranch, then north-east across Walnut '
                'Creek to the valley road at bench mark 5049. Dashed on the sheet.',
        'parts': [('animas', [(594, 4225), (663, 4319), (694, 4375), (700, 4419), (681, 4494), (738, 4550),
                              (775, 4581), (931, 4525), (1038, 4481), (1144, 4413), (1250, 4350), (1450, 4325),
                              (1675, 4338), (1775, 4388), (1875, 4419), (1975, 4394), (2088, 4438), (2138, 4481),
                              (2300, 4478), (2450, 4463), (2523, 4478)])],
    },
    {
        'id': 'road-clanton-draw',
        'class': 'trail',
        'certainty': 'approximate',
        'first_seen': '1-01',
        'book_name': None,
        'note': 'From the Field Ranch east down Clanton Draw towards the valley road below the Gray Ranch. Dashed '
                'on the sheet; the eastern end, where several dashed roads meet, is not clear on the scan.',
        'parts': [('animas', [(806, 5069), (838, 5113), (1000, 5163), (1225, 5210), (1375, 5248), (1563, 5260),
                              (1744, 5248), (1800, 5219), (1913, 5100), (2063, 5088), (2181, 5081), (2238, 5113),
                              (2350, 5138), (2556, 5075)])],
    },
]


def to_lonlat(sheet: str, col: float, row: float) -> tuple[float, float]:
    ox, pw, oy, ph = SHEETS[sheet]['transform']
    x, y = ox + (col + 0.5) * pw, oy + (row + 0.5) * ph
    lon, lat = TO_WGS84.transform(x, y)
    return round(lon, 6), round(lat, 6)


def length_mi(line: LineString) -> float:
    return GEOD.geometry_length(line) / 1609.344


def butterfield() -> dict:
    data = json.loads(BUTTERFIELD.read_text())
    merged = linemerge(unary_union([shape(f['geometry']) for f in data['features']]))
    # Simplified to 0.0004 deg (about 40 m), under the 1:100,000 the NPS digitised at; the finer wiggles kept the
    # name from fitting along the line in the lab.
    clipped = merged.intersection(BUTTERFIELD_BOX).simplify(0.0004)
    return {
        'type': 'Feature',
        'properties': {
            'id': 'road-butterfield',
            'name': 'Butterfield Overland National Historic Trail',
            'class': 'trail',
            'source': 'NPS National Trails, Butterfield Overland NHT designated alignment, 2026 (DataStore 2318550)',
            'source_licence': 'Public domain (US federal work). Credit: National Park Service, National Trails '
                              'Intermountain Region.',
            'certainty': 'approximate',
            'first_seen': '1-01',
            'book_name': None,
            'note': "The 1858-61 stage road through Stein's Pass and Lordsburg, about 32.2 deg N: north of the test "
                    'area, so clipped to a box widened to 32.4 deg N. NPS digitised it at 1:100,000 or larger and '
                    'says it does not always follow the historic trace.',
        },
        'geometry': json.loads(json.dumps(mapping(clipped))),
    }


def main() -> None:
    print('Sheets: American Polyconic on NAD27; to WGS 84 by the CONUS Helmert shift (EPSG:1173)')
    features = []
    for road in ROADS:
        coords: list[tuple[float, float]] = []
        sources = []
        for sheet, pts in road['parts']:
            coords += [to_lonlat(sheet, c, r) for c, r in pts]
            sources.append(SHEETS[sheet]['source'])
        line = LineString(coords)
        props = {
            'id': road['id'],
            'name': None,
            'class': road['class'],
            'source': '; '.join(sources),
            'source_licence': LICENCE,
            'certainty': road['certainty'],
            'first_seen': road['first_seen'],
            'book_name': road['book_name'],
            'note': road['note'],
        }
        if 'mileage' in road:
            props['mileage'] = road['mileage']
            props['mileage_ref'] = road['mileage_ref']
        print(f"{road['id']:32} {length_mi(line):5.1f} mi, {len(coords)} vertices")
        if road['id'] == 'road-animas-valley':
            # Split at the SK Bar so the mileage label sits on the stretch the book measures.
            at = line.project(Point(SK_BAR))
            start = line.project(Point(CLOVERDALE))
            south, north = substring(line, start, at), substring(line, at, line.length)
            print(f'  Cloverdale to the SK Bar along the road: {length_mi(south):.1f} mi (book: nine miles)')
            features.append({'type': 'Feature', 'properties': {**props, 'id': 'road-animas-valley-south'},
                             'geometry': mapping(south)})
            rest = {k: v for k, v in props.items() if k not in ('mileage', 'mileage_ref')}
            features.append({'type': 'Feature', 'properties': {**rest, 'id': 'road-animas-valley-north'},
                             'geometry': mapping(north)})
            continue
        if road['id'] == 'road-cloverdale-creek':
            print('  whole road from Cloverdale to the sheet edge; the book gives four miles from a spring on it')
        features.append({'type': 'Feature', 'properties': props, 'geometry': mapping(line)})
    trail = butterfield()
    print(f"road-butterfield (clipped)       {length_mi(shape(trail['geometry'])):5.1f} mi")
    features.append(trail)

    write(SEED, features)
    write(LAB, features + [mileage_point(f) for f in features if 'mileage' in f['properties']])


def mileage_point(feature: dict) -> dict:
    """A point at the middle of a measured stretch, with the angle to set its mileage along the line.

    The lab draws the mileage from this point rather than from the line: a GeoJSON source cuts lines at tile
    edges, and MapLibre's line-center placement would letter each piece.
    """
    line = shape(feature['geometry'])
    mid = line.interpolate(0.5, normalized=True)
    a, b = line.interpolate(max(0, line.project(mid) - 0.002)), line.interpolate(line.project(mid) + 0.002)
    # Web Mercator stretches north-south distances by 1 / cos(lat); MapLibre's text-rotate is clockwise in degrees.
    dx, dy = b.x - a.x, (b.y - a.y) / math.cos(math.radians(mid.y))
    angle = -math.degrees(math.atan2(dy, dx))
    angle = angle - 180 if angle > 90 else angle + 180 if angle < -90 else angle
    p = feature['properties']
    return {
        'type': 'Feature',
        'properties': {'id': f"{p['id']}-mileage", 'mileage': p['mileage'], 'angle': round(angle, 1),
                       'first_seen': p['first_seen']},
        'geometry': {'type': 'Point', 'coordinates': [round(mid.x, 6), round(mid.y, 6)]},
    }


def write(path: Path, features: list[dict]) -> None:
    # One feature a line, so a diff of the seed shows which road changed.
    rows = ',\n'.join(json.dumps(f, ensure_ascii=False, separators=(',', ':')) for f in features)
    text = '{"type":"FeatureCollection","features":[\n' + rows + '\n]}\n'
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)
    print(f'wrote {path.relative_to(ROOT)} ({len(text) / 1024:.0f} KB)')


if __name__ == '__main__':
    main()
