"""Download the CEC's North American Land Cover 2020 (30 m, version 2) for Mexico and the US (decision 0040).

Run from the repo root: uv run --project pipeline python -m crossing.fetch_landcover

The CEC ships each country's GeoTIFF deflated inside a zip, so GDAL cannot read a window of it remotely. For each
zip this reads the central directory (one ranged request), then downloads only the entries it needs (one ranged
request each) and inflates them into private/cache/landcover/cec/: mex.tif and usa.tif, and from the Mexico zip
the CEC's citation note and terms of use. Files already there are skipped, so a rerun makes no requests. Every
request is logged in requests.log beside the data. curl makes the requests, because it trusts the system's
certificates.

Source: Commission for Environmental Cooperation, North American Land Cover 2020 (Landsat, 30 m),
https://www.cec.org/north-american-environmental-atlas/land-cover-30m-2020/
"""

import struct
import subprocess
import zlib
from datetime import UTC, datetime
from pathlib import Path

from crossing.paths import CACHE

CEC = CACHE / "landcover" / "cec"
BASE = "https://www.cec.org/files/atlas_layers/1_terrestrial_ecosystems/1_01_0_land_cover_2020_30m/"
# For each zip, the entries wanted (by the end of their path) and the file each becomes.
WANTED = {
    "mex_land_cover_2020v2_30m_tif.zip": {
        "MEX_NALCMS_landcover_2020v2_30m.tif": "mex.tif",
        "HowToCite_ComoCitar_CommentCiter.txt": "how-to-cite.txt",
        "Terms of use.doc": "terms-of-use.doc",
    },
    "usa_land_cover_2020v2_30m_tif.zip": {"USA_NALCMS_landcover_2020v2_30m.tif": "usa.tif"},
}


def ranged(url: str, span: str, to: Path) -> None:
    with (CEC / "requests.log").open("a") as log:
        log.write(f"{datetime.now(UTC):%Y-%m-%dT%H:%M:%SZ}\tGET\t{url}\tRange: bytes={span}\n")
    subprocess.run(["curl", "-sSf", "-A", "Mozilla/5.0", "-r", span, url, "-o", str(to)], check=True)


def directory(tail: bytes) -> dict[str, tuple[int, int, int]]:
    """Each entry's name, and its compression method, local header offset and compressed size, from the end of a
    zip (its central directory)."""
    out, i = {}, 0
    while (i := tail.find(b"PK\x01\x02", i)) >= 0:
        method = struct.unpack("<H", tail[i + 10 : i + 12])[0]
        size = struct.unpack("<I", tail[i + 20 : i + 24])[0]
        n = struct.unpack("<H", tail[i + 28 : i + 30])[0]
        offset = struct.unpack("<I", tail[i + 42 : i + 46])[0]
        out[tail[i + 46 : i + 46 + n].decode()] = (method, offset, size)
        i += 4
    return out


def extract(url: str, method: int, offset: int, size: int, to: Path) -> None:
    """One entry of a remote zip, inflated to `to`."""
    part = to.with_suffix(".part")
    # The local header is 30 bytes plus its name and extra field; 64 KB more covers both.
    ranged(url, f"{offset}-{offset + size + 65536}", part)
    with part.open("rb") as f, to.with_suffix(".tmp").open("wb") as out:
        n, m = struct.unpack("<HH", f.read(30)[26:30])
        f.seek(30 + n + m)
        if method == 0:
            out.write(f.read(size))
        else:
            inflate = zlib.decompressobj(-15)
            while (chunk := f.read(1 << 22)) and not inflate.eof:
                out.write(inflate.decompress(chunk))
    to.with_suffix(".tmp").rename(to)
    part.unlink()


def main() -> None:
    CEC.mkdir(parents=True, exist_ok=True)
    for zipname, wanted in WANTED.items():
        missing = {end: name for end, name in wanted.items() if not (CEC / name).exists()}
        if not missing:
            continue
        url = BASE + zipname
        tail = CEC / f"{zipname}.directory"
        ranged(url, "-65536", tail)
        entries = directory(tail.read_bytes())
        tail.unlink()
        for end, name in missing.items():
            path = next((p for p in entries if p.endswith(end)), None)
            if path is None:
                raise SystemExit(f"{end} is not in {zipname}")
            extract(url, *entries[path], CEC / name)
            print(f"wrote {CEC / name}", flush=True)


if __name__ == "__main__":
    main()
