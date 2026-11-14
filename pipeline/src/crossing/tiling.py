"""Running tippecanoe for the published archives."""

import subprocess
from collections.abc import Sequence
from pathlib import Path


def tippecanoe(folder: Path, out: str, layers: Sequence[tuple[str, str]], *, zooms: tuple[int, int], name: str,
               attribution: str, description: str | None = None, extra: Sequence[str] = ()) -> Path:
    """Tile `layers`, (layer name, GeoJSON file name in `folder`) pairs, into `folder`/`out`.

    tippecanoe runs inside `folder` with relative file names because it records its command line in the
    archive's metadata, and the archives are published: absolute paths would leak local folders.
    """
    args = ["tippecanoe", "-q", "-f", "-o", out, f"-Z{zooms[0]}", f"-z{zooms[1]}", "--no-tile-size-limit",
            "-n", name, *(["-N", description] if description else []), "-A", attribution, *extra]
    args += [a for layer, file in layers for a in ("-L", f"{layer}:{file}")]
    subprocess.run(args, check=True, cwd=folder)
    return folder / out
