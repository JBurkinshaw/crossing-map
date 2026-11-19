# 0064. A size budget for the Pages site, checked in CI

Status: accepted (2026-11-18)
Phase: P1

## Context

GitHub Pages publishes at most 1 GB. One Pages site holds two builds: `main` at the root and the newest stage branch under `/preview/` (decision 0003). Each build ships the tile release its branch pins in `tiles/release.txt`, unless both pin the same tag, when the preview reads the root's tiles (`docs/releasing-tiles.md`, section 4).

`tiles-v12` is 540 MB. Once `main` pins it and the preview moves on to a newer release of about the same size, the two builds together pass 1 GB. Nothing checked this before the Pages upload, so the first sign would have been a failed deploy.

## Decision

- **The `build` job in `.github/workflows/deploy.yml` measures `_site` after both builds and before the upload.** It always prints the size, the budget and the two tile tags.
- **The budget is 900 MB,** which leaves 10% of the Pages limit free for the site's own files, the data downloads and a margin. Over it, the step fails with an error naming both tags and how to share one release.
- The size is measured with `du -sb` on the runner (GNU coreutils), in bytes, as Pages counts files.

## Alternatives

- **Check the release asset sizes in the `check` job.** It would fail about 12 minutes sooner, before the spoiler-leak test, but it needs the GitHub API, both branches' `release.txt` files and a sum. The size of the built folder is the number Pages actually limits, and one `du` measures it.
- **A warning instead of a failure.** Pages would refuse the upload anyway, with a less clear message.
- **A lower budget, such as 800 MB.** It would fail on sizes Pages still accepts and force a release split sooner than needed.

## Consequences

- A release that would push the site past 900 MB fails the deploy with a clear message, and the site already live stays up.
- Every deploy log shows how much of the budget is used.
- The fix for a failure is to pin one tag on both branches, drop archives the site no longer reads (as `relief.pmtiles` and `relief-dense.pmtiles` in `tiles-v12`), or move tiles off Pages (roadmap, Cloudflare R2).
