# 0003. Host on GitHub Pages

Status: accepted (2026-11-11)
Phase: P1

## Context

A static site with a few PMTiles archives, a free budget, and one maintainer.

## Decision

GitHub Pages, deployed by GitHub Actions (`.github/workflows/deploy.yml`). One Pages site holds two builds: `main` at `/crossing-map/` and the newest `stage/*` branch at `/crossing-map/preview/`.

Limits from GitHub's docs, checked 2026-11-11: 1 GB published site, 10-minute deployment timeout, soft 100 GB a month of bandwidth.

## Alternatives

- Cloudflare Pages: 25 MiB file limit, and its docs do not state range-request support.
- S3 or Cloudflare R2: more setup than P1 needs. R2 is the P2 move if tiles outgrow Pages.

## Consequences

$0 a month. One preview slot, which suits a one-person project. The `github-pages` environment allows deployments from `main` and `stage/*` only.
