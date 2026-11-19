# Releasing tiles

The PMTiles archives are built on the owner's machine and published as assets of a GitHub Release tagged `tiles-vN` (decision 0004). A branch pins its release in `tiles/release.txt`, and the deploy downloads that release. Nothing in `tiles/out/` is committed.

## 1. Build

Rebuild only the archives whose inputs changed. The commands are in [`pipeline.md`](pipeline.md), sections 5 and 6.

| Archive | Built by |
| --- | --- |
| `base.pmtiles` | `tiles.build_base` |
| `contours.pmtiles` | `crossing.hachures`, then `tiles.build_relief` |
| `relief-wheeler.pmtiles`, `relief-wheeler-12.pmtiles` | `crossing.hachures` (for the coarse strokes), `crossing.hachures --style wheeler --region corridor`, then `tiles.build_relief --style wheeler --region corridor` |
| `terrain.pmtiles` | `tiles.build_terrain` |
| `oblique-1.pmtiles` to `oblique-3.pmtiles`, `landcover.pmtiles` | `crossing.hachures` (for its tile grid) and `crossing.fetch_landcover`, then `crossing.plan_oblique` |

The site's hachures are all in `relief-wheeler*.pmtiles`: the Wheeler strokes inside the journeys corridor and the coarse strokes outside it (decision 0024). `relief.pmtiles` and `relief-dense.pmtiles` were dropped after `tiles-v11`. Don't release them.

`crossing.plan_oblique` also rewrites `data/oblique/*.geojson` and `data/oblique/archives.json`, which list the Oblique archives in drawing order. Commit those with the release bump: the site draws every archive the list names, and only those.

## 2. Check

1. Copy the archives into the local site and look at them:

   ```bash
   uv run --project pipeline python -m tiles.install
   (cd site && npm run dev)
   ```

2. Check every asset is under 100 MB, the limit this project keeps for each file:

   ```bash
   ls -l tiles/out/*.pmtiles
   ```

   `tiles.build_relief` and `crossing.plan_oblique` split their output to stay under it. If an archive still passes it, split it before releasing.

3. Check the total. GitHub Pages publishes at most 1 GB, and the root and the preview each carry their tiles unless they share a release (section 4). The deploy fails if the built site passes 900 MB (decision 0064), so check before you publish rather than after.

## 3. Publish

Warning: a release is public as soon as it is created.

1. Pick the next tag: one more than the number in `tiles/release.txt`.
2. Create the release with every archive the site reads, changed or not, so one tag holds a complete set:

   ```bash
   gh release create tiles-vN \
     tiles/out/base.pmtiles \
     tiles/out/relief-wheeler.pmtiles \
     tiles/out/relief-wheeler-12.pmtiles \
     tiles/out/contours.pmtiles \
     tiles/out/terrain.pmtiles \
     tiles/out/oblique-1.pmtiles \
     tiles/out/oblique-2.pmtiles \
     tiles/out/oblique-3.pmtiles \
     tiles/out/landcover.pmtiles \
     --title "Tiles vN: <what changed>" \
     --notes "<what changed, and each archive's sources>"
   ```

   An archive not rebuilt this time can be downloaded from the previous release first: `gh release download tiles-vM --pattern '<name>.pmtiles' --dir tiles/out`.

3. Write the new tag into `tiles/release.txt`.
4. Add a line under Unreleased in [`CHANGELOG.md`](CHANGELOG.md) naming the tag and what readers will see.
5. Commit `tiles/release.txt`, the changelog, and any changed `data/oblique/` files together, then push the branch.

## 4. How the deploy uses it

`.github/workflows/deploy.yml` reads `tiles/release.txt` on `main` and on the preview branch, and downloads each distinct tag once into the runner's temp folder. It passes that folder to `tools/build-site.sh` as its fourth argument, so the build links the archives in instead of downloading them again.

When the preview pins the same tag as `main`, the preview build sets `VITE_TILES_BASE=/crossing-map/tiles/`. The preview then reads the root site's archives and ships none of its own, which halves the tile weight of the Pages artifact.

Run locally, `tools/build-site.sh <checkout> <base> <out>` with no fourth argument downloads the pinned release itself with `gh`.

## Pending

- The Oblique archives and `landcover.pmtiles` need a release (decision 0040). See [`roadmap.md`](roadmap.md).
