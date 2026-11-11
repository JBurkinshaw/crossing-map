# 0004. Tiles ship as GitHub Release assets

Status: accepted (2026-11-11)
Phase: P1

## Context

PMTiles archives are built locally. The relief step needs QGIS and can run for hours, so CI cannot build them. Committing binary archives would grow git history with every rebuild, and git rejects files over 100 MB.

## Decision

Built archives are git-ignored. Each tile build is uploaded to a GitHub Release tagged `tiles-vN`. `tiles/release.txt` names the release a branch uses, and `tools/build-site.sh` downloads its `*.pmtiles` assets into the site before building.

## Alternatives

- Commit the archives: history bloat and the 100 MB push limit.
- Git LFS: storage and bandwidth quotas, and more setup.
- Build tiles in CI: needs QGIS, large elevation downloads, and long runs.

## Consequences

Tiles are versioned and a branch pins its tile set. Release assets allow 2 GB per file. Publishing tiles is a manual `gh release create` after a local build.
