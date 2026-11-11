#!/usr/bin/env bash
# Build one checkout of the site into an output folder.
# Usage: tools/build-site.sh <checkout-dir> <base-path> <out-dir>
# Example: tools/build-site.sh . /crossing-map/ _site
# Tiles are not in git: the release named in tiles/release.txt is downloaded
# into site/public/tiles first. Needs `gh` with GH_TOKEN set.
set -euo pipefail

checkout=$(cd "$1" && pwd)
base=$2
out=$3
mkdir -p "$out"
out=$(cd "$out" && pwd)

tiles_dir="$checkout/site/public/tiles"
mkdir -p "$tiles_dir"
tag=$(tr -d '[:space:]' < "$checkout/tiles/release.txt")
gh release download "$tag" --repo "${GITHUB_REPOSITORY:-JBurkinshaw/crossing-map}" \
  --pattern '*.pmtiles' --dir "$tiles_dir" --clobber

cd "$checkout/site"
npm ci --no-audit --no-fund
VITE_BASE="$base" npm run build
cp -R dist/. "$out/"
