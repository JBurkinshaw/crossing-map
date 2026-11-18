import math

from shapely.geometry import Point

from crossing import build_vignettes
from crossing.build_vignettes import MERC, Story, footprint, journey_of, place, px_per_m, shown_from


def feature(lon: float, lat: float, **props) -> dict:
    return {"type": "Feature", "geometry": {"type": "Point", "coordinates": [lon, lat]}, "properties": props}


def line(*coords) -> dict:
    return {"type": "Feature", "geometry": {"type": "LineString", "coordinates": list(coords)}, "properties": {}}


def test_footprint_matches_relief_ts():
    # At zoom 9 the icon size is 0.72: east puts the drawing's left edge 16 x 0.72 px right of the point.
    (x0, y0, x1, y1), = footprint("e", 9, "")
    assert (round(x0, 2), round(y0, 2), round(x1, 2), round(y1, 2)) == (11.52, -34.56, 80.64, 34.56)
    # A caption goes under the drawing, 2 px below it.
    drawing, caption = footprint("n", 9, "A caption")
    assert caption[1] == drawing[3] + 2


def offset(lon: float, lat: float, dx_px: float, dy_px: float, z: float) -> tuple[float, float]:
    """The lon and lat dx px east and dy px south of a point at zoom z."""
    x, y = MERC.transform(lon, lat)
    scale = px_per_m(z)
    return MERC.transform(x + dx_px / scale, y - dy_px / scale, direction="INVERSE")


def test_picks_the_clear_side_and_keeps_the_seed_side_on_a_tie():
    lon, lat = -108.0, 30.0
    # A stop 50 px east of the point at zoom 9 and a route line running away west.
    stops = [feature(*offset(lon, lat, 50, 0, 9), id="s1", journey="J1", place_ref=None)]
    story = Story(stops, [], [line((lon, lat), offset(lon, lat, -300, 0, 9))])
    at = Point(MERC.transform(lon, lat))
    d, clash = place(story, at, "e", 9, "")
    assert clash.clear and d.zoom == 9
    # The diagonal sides' corners still reach the stop's marker, so the nearest clear sides to the seed's are n and s.
    assert d.side in {"n", "s"}


def test_a_hub_crowded_at_every_zoom_keeps_its_first_zoom():
    lon, lat = -108.0, 30.0
    spokes = [line((lon, lat), offset(lon, lat, dx * 3000, dy * 3000, 9))
              for dx in (-1, 0, 1) for dy in (-1, 0, 1) if dx or dy]
    story = Story([], [], spokes)
    d, clash = place(story, Point(MERC.transform(lon, lat)), "w", 8, "")
    assert d.zoom == 8 and not clash.clear


def test_waits_at_most_one_zoom_step(monkeypatch):
    lon, lat = -108.0, 30.0
    # A ring of stops 80 px out at zoom 9: every side covers one at zooms 8 and 9, none at 10.
    ring = [feature(*offset(lon, lat, 80 * math.cos(a), 80 * math.sin(a), 9), id=f"s{k}", journey="J1", place_ref=None)
            for k, a in enumerate(math.radians(d) for d in range(0, 360, 45))]
    story = Story(ring, [], [])
    at = Point(MERC.transform(lon, lat))
    d, clash = place(story, at, "e", 8, "")
    assert d.zoom == 9 and not clash.clear
    # Without the cap it would wait for zoom 10.
    monkeypatch.setattr(build_vignettes, "MAX_RISE", 99)
    d, clash = place(story, at, "e", 8, "")
    assert d.zoom == 10 and clash.clear


def test_journey_of_a_place_is_its_first_stop_in_reading_order():
    stops = [feature(0, 0, id="j3-a", journey="J3", sequence=2, first_seen="2-05", place_ref="place-a"),
             feature(0, 0, id="j2-a", journey="J2", sequence=5, first_seen="1-08", place_ref="place-a"),
             feature(1, 1, id="j4-b", journey="J4", sequence=1, first_seen="2-08", place_ref=None)]
    places = {"place-a": feature(0, 0), "place-c": feature(1.01, 1.01)}
    assert journey_of("j3-a", "1-01", stops, places) == "J3"
    assert journey_of("place-a", "1-01", stops, places) == "J2"
    # No stop at the place: the nearest stop of the drawing's own episode.
    assert journey_of("place-c", "2-08", stops, places) == "J4"


def test_a_drawing_waits_for_its_pin():
    pin = feature(0, 0, first_seen="2-05")
    assert shown_from("1-02", pin) == "2-05"
    assert shown_from("3-01", pin) == "3-01"
