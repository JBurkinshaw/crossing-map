# 0011. Elevation: Terrain Tiles for display, Copernicus for analysis

Status: accepted (2026-11-11)
Phase: P1

## Context

Relief needs elevation twice: once in the pipeline, to generate hachures and find peaks, and once in the browser, if the relief experiment keeps a hillshade. AWS Terrain Tiles (Mapzen/Tilezen) offer a ready global mosaic in web tiles. Each tile's `x-amz-meta-x-imagery-sources` header shows what it is built from. Near Cloverdale it is USGS NED at 1/9 arc-second (about 3 m); in Sonora it is SRTM (about 30 m); near Casas Grandes it is INEGI lidar mixed with SRTM. All tiles were last modified in 2016–2017, and the project's docs say "regular updates are not planned".

## Decision

- **Display:** download Terrain Tiles (Terrarium PNG) for the story box once, at zoom 5–10 (1,171 tiles, about 63 MB), and repack them into a raster-dem PMTiles archive served with the rest of the site. MapLibre shades it with a `hillshade` layer, `hillshade-method: "multidirectional"`.
- **Analysis:** generate hachures and find peaks from Copernicus GLO-30, 1° COG tiles on AWS open data with no login. Start with the tiles under the journeys corridor.

## Alternatives

- **Link the browser straight to the Terrain Tiles bucket.** Rejected: the docs say the S3 tiles are "meant for efficient networking with EC2 resources only"; there is no CDN, no guarantee the bucket stays up, and the plan wants the literary map to work without third-party services.
- **Terrain Tiles for hachures.** Rejected: the mix of 3 m, 10 m, lidar and 30 m sources would change hachure spacing and texture at every source boundary, because Huffman's method spaces lines in pixels and scales slope to each raster's range. The tiles are also in Web Mercator.
- **Pre-rendered hillshade images (`gdaldem`).** Rejected: every change of light, tint or opacity would be a rebuild.
- **NASADEM.** Similar to Copernicus, but needs an Earthdata login; Copernicus is newer and does not.

## Consequences

Two attribution sets: the Terrain Tiles lines (USGS; INEGI) wherever the hillshade shows, and the Copernicus notice on the Credits page for derived hachures. One download batch of about 1,200 tile requests, to be approved in stage 3. The same raster-dem archive could later drive 3D terrain.
