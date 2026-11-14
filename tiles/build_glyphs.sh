#!/usr/bin/env bash
# Build MapLibre glyphs (SDF PBF) from the IM Fell fonts the style uses into site/public/fonts/.
# Usage: tiles/build_glyphs.sh   (needs build_pbf_glyphs: cargo install build_pbf_glyphs)
# The fonts are OFL; the glyphs are committed in site/public with the licence because CI has no Rust.
# Roman and italic are the style's text fonts (site/src/map/tokens.ts); small capitals are kept for state labels.
# Only the ranges a Latin-script map needs are kept: Basic Latin and Latin-1 (0-255),
# Latin Extended (256-767), and General Punctuation (8192-8447) for ’ – and “ ”.
set -euo pipefail

repo=$(cd "$(dirname "$0")/.." && pwd)
fonts="$repo/private/cache/basemap/fonts"
out="$repo/site/public/fonts"
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT

mkdir -p "$tmp/src" "$tmp/pbf" "$tmp/out"
cp "$fonts/IMFeENrm28P.ttf" "$fonts/IMFeENit28P.ttf" "$fonts/IMFeENsc28P.ttf" "$tmp/src/"
PATH="$HOME/.cargo/bin:$PATH" build_pbf_glyphs "$tmp/src" "$tmp/pbf"
for dir in "$tmp"/pbf/*/; do
  name=$(basename "$dir")
  mkdir -p "$tmp/out/$name"
  for range in 0-255 256-511 512-767 8192-8447; do
    cp "$dir/$range.pbf" "$tmp/out/$name/"
  done
done
cp "$fonts/OFL.txt" "$tmp/out/OFL.txt"
# The committed glyphs are replaced only once the whole set has built.
rm -rf "$out"
mv "$tmp/out" "$out"
ls "$out"
du -sh "$out"
