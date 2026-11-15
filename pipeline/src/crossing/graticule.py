"""A 15-minute graticule over the story box, for the map and the Wheeler lab.

Run from the repo root:
    uv run --project pipeline python -m crossing.graticule

Wheeler's sheet 70A rules a graticule line every 15′ across the map and labels it in the margin (30′, 15′, and
the whole degree as 105°); review/stage-8/wheeler/README.md, finding 16. This writes those lines for the whole
story box to site/public/labels/graticule.geojson. Web Mercator draws meridians and parallels as straight
lines, so each line needs only its two end points.

Properties: `axis` (lat or lon), `deg` (the value in decimal degrees, west negative), `label` ("31°15′ N"),
`short` (Wheeler's margin form: "15′", or "31°" on a whole degree), `rank` (1 a whole degree, 2 a half degree,
3 a quarter) and `first_seen` 1-01, as a context feature.
"""

import json

from crossing.paths import SITE_PUBLIC, STORY_BOX

OUT = SITE_PUBLIC / "labels" / "graticule.geojson"
STEP_MIN = 15


def labels(minutes: int, hemi: str) -> tuple[str, str]:
    d, m = divmod(abs(minutes), 60)
    full = f"{d}°{m:02d}′ {hemi}" if m else f"{d}° {hemi}"
    return full, f"{m}′" if m else f"{d}°"


def lines() -> list[dict]:
    w, s, e, n = STORY_BOX
    out = []
    for axis, lo, hi in (("lon", w, e), ("lat", s, n)):
        for minutes in range(round(lo * 60), round(hi * 60) + 1, STEP_MIN):
            deg = minutes / 60
            hemi = ("W" if minutes < 0 else "E") if axis == "lon" else ("S" if minutes < 0 else "N")
            full, short = labels(minutes, hemi)
            rank = 1 if minutes % 60 == 0 else 2 if minutes % 30 == 0 else 3
            coords = [[deg, s], [deg, n]] if axis == "lon" else [[w, deg], [e, deg]]
            out.append({"type": "Feature", "geometry": {"type": "LineString", "coordinates": coords},
                        "properties": {"axis": axis, "deg": round(deg, 4), "label": full, "short": short, "rank": rank,
                                       "first_seen": "1-01"}})
    return out


def main() -> None:
    feats = lines()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    fc = {"type": "FeatureCollection", "features": feats}
    OUT.write_text(json.dumps(fc, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    print(f"{len(feats)} lines -> {OUT}")


if __name__ == "__main__":
    main()
