"""Shared locations and extents for every pipeline, tile and art script."""

from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
DATA = REPO / "data"
SEEDS = REPO / "pipeline" / "seeds"
PRIVATE = REPO / "private"
CACHE = PRIVATE / "cache"
SITE_PUBLIC = REPO / "site" / "public"
TILES_OUT = REPO / "tiles" / "out"

# The story box (design section 7): west, south, east, north in degrees.
STORY_BOX = (-113.0, 27.0, -104.0, 36.0)
# The story box widened by half a degree, so base-map lines run off the edge cleanly.
STORY_BOX_PADDED = (-113.5, 26.5, -103.5, 36.5)
# UTM zone 12N: the bootheel and eastern Sonora; Chihuahua lies just east of the zone. The relief, the Raised view
# and the summit search all work in it.
UTM_CRS = "EPSG:32612"
