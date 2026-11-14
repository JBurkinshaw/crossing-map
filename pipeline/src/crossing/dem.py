"""The Copernicus GLO-30 elevation tiles cached in private/, a VRT mosaic over them, and downloads of elevation data."""

import subprocess
import time
import urllib.error
import urllib.request
from pathlib import Path

from crossing.paths import CACHE

# The story box's corridor tiles, and the rest of the story box that `crossing.fetch_dem --story-box` adds.
COPERNICUS = CACHE / "dem" / "copernicus"
COPERNICUS_REGION = CACHE / "dem" / "copernicus-region"
# The licence notice for every product drawn from the Copernicus DEM.
NOTICE = ("Copernicus DEM GLO-30, © DLR e.V. 2010-2014 and © Airbus Defence and Space GmbH 2014-2018, "
          "provided under COPERNICUS by the European Union and ESA")
USER_AGENT = "crossing-map-pipeline/0.1"


def tiles(*folders: Path) -> list[Path]:
    """Every GeoTIFF in the folders, sorted, so a mosaic is the same on every run."""
    return sorted(t for folder in folders for t in folder.glob("*.tif"))


def build_vrt(out: Path, sources: list[Path]) -> Path:
    """Write a GDAL VRT mosaic of the sources to `out` and return it."""
    subprocess.run(["gdalbuildvrt", "-q", str(out), *map(str, sources)], check=True)
    return out


def download(url: str, path: Path, timeout: float = 120, attempts: int = 3) -> None:
    """Save `url` to `path`, retrying network errors and server errors with a growing pause. A client error
    (4xx) is raised at once: retrying will not change it."""
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    for attempt in range(1, attempts + 1):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                data = r.read()
            break
        except urllib.error.HTTPError as e:
            if e.code < 500 or attempt == attempts:
                raise
        except (urllib.error.URLError, TimeoutError):
            if attempt == attempts:
                raise
        time.sleep(2**attempt)
    path.parent.mkdir(parents=True, exist_ok=True)
    # Written in one go after a complete read, so a failed download leaves no partial tile for the cache to skip.
    path.write_bytes(data)
