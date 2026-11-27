#!/usr/bin/env bash
# Build one checkout of the site into an output folder.
# Usage: tools/build-site.sh <checkout-dir> <base-path> <out-dir> [tiles-dir]
# Example: tools/build-site.sh . / _site
#
# Tiles are not in git (decision 0004). With a tiles-dir, its archives are linked into site/public/tiles, so CI
# downloads each release once for every build that uses it. Without one, the release named in
# tiles/release.txt is downloaded with `gh` (GH_TOKEN set in CI, or `gh auth login` locally).
#
# With VITE_TILES_BASE set (an absolute path such as /tiles/), the site reads its tiles from there
# and this build ships none of its own. If the built bundle does not contain that path, the site ignored the
# variable, so the tiles are copied in after all and a warning is printed.
set -euo pipefail

checkout=$(cd "$1" && pwd)
base=$2
out=$3
tiles=${4:-}
mkdir -p "$out"
out=$(cd "$out" && pwd)

tiles_dir="$checkout/site/public/tiles"
fetch_tiles() {
  mkdir -p "$tiles_dir"
  if [ -n "$tiles" ]; then
    # Hard links where the filesystem allows, so a second build costs no disk.
    cp -l "$tiles"/*.pmtiles "$tiles_dir"/ 2>/dev/null || cp "$tiles"/*.pmtiles "$tiles_dir"/
  else
    tag=$(tr -d '[:space:]' < "$checkout/tiles/release.txt")
    gh release download "$tag" --repo "${GITHUB_REPOSITORY:-JBurkinshaw/crossing-map}" \
      --pattern '*.pmtiles' --dir "$tiles_dir" --clobber
  fi
}

if [ -z "${VITE_TILES_BASE:-}" ]; then fetch_tiles; fi

cd "$checkout/site"
npm ci --no-audit --no-fund --ignore-scripts
VITE_BASE="$base" npm run build
cp -R dist/. "$out/"

if [ -n "${VITE_TILES_BASE:-}" ] && ! grep -rqF "$VITE_TILES_BASE" dist/assets; then
  echo "::warning::The site ignored VITE_TILES_BASE; copying the tiles into $out/tiles instead."
  fetch_tiles
  mkdir -p "$out/tiles"
  cp "$tiles_dir"/*.pmtiles "$out/tiles/"
fi
