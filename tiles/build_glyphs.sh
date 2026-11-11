#!/usr/bin/env bash
# Build MapLibre glyphs (SDF PBF) from the IM Fell fonts into site/public/fonts/.
# Usage: tiles/build_glyphs.sh   (needs build_pbf_glyphs: cargo install build_pbf_glyphs)
# The fonts are OFL; the glyphs are committed with the licence because CI has no Rust.
# Only the ranges a Latin-script map needs are kept: Basic Latin and Latin-1 (0-255),
# Latin Extended (256-767), and General Punctuation (8192-8447) for ’ – and “ ”.
set -euo pipefail

repo=$(cd "$(dirname "$0")/.." && pwd)
fonts="$repo/private/cache/basemap/fonts"
out="$repo/site/public/fonts"
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT

PATH="$HOME/.cargo/bin:$PATH" build_pbf_glyphs "$fonts" "$tmp"
rm -rf "$out"
mkdir -p "$out"
for dir in "$tmp"/*/; do
  name=$(basename "$dir")
  mkdir -p "$out/$name"
  for range in 0-255 256-511 512-767 8192-8447; do
    cp "$dir/$range.pbf" "$out/$name/"
  done
done
cp "$fonts/OFL.txt" "$out/OFL.txt"
ls "$out"
du -sh "$out"
