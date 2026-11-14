"""Tile builds. Run each as a module from the repo root, for example:
    uv run --project pipeline python -m tiles.build_base
"""

# The zooms base.pmtiles is built for; creeks.py caps each creek's first zoom at the deepest.
BASE_ZOOMS = (4, 11)
