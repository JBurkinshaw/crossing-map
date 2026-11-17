"""Copy the archives built in tiles/out/ into the local site, for the dev server and local builds.

Run from the repo root: uv run --project pipeline python -m tiles.install
The published site does not use this: tools/build-site.sh downloads the release named in tiles/release.txt.
Oblique-view archives in site/public/tiles that data/oblique/archives.json no longer lists are removed, so a rebuilt
Oblique view with fewer parts leaves no stale archive behind.
"""

import json
import shutil

from crossing.paths import DATA, SITE_PUBLIC, TILES_OUT

SITE_TILES = SITE_PUBLIC / "tiles"


def main() -> None:
    SITE_TILES.mkdir(parents=True, exist_ok=True)
    oblique = set(json.loads((DATA / "oblique" / "archives.json").read_text()))
    for old in SITE_TILES.glob("oblique*.pmtiles"):
        if old.name not in oblique:
            old.unlink()
            print(f"Removed {old.name}")
    for archive in sorted(TILES_OUT.glob("*.pmtiles")):
        shutil.copy2(archive, SITE_TILES / archive.name)
        print(f"Copied {archive.name} ({archive.stat().st_size / 1e6:.1f} MB)")


if __name__ == "__main__":
    main()
