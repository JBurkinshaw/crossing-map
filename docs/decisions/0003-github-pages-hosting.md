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

## Amendment, 2026-11-27: a custom domain

The site moves to `thecrossingmap.com`, registered with Porkbun, so that its address names the book and can stay put whatever the host. The owner chose Porkbun over Cloudflare Registrar, which costs about $3 less over five years, to keep the domain and its DNS apart from Cloudflare. `main` is now served at `/` and the preview at `/preview/`.

- **Where the address lives.** The repository variable `SITE_URL` holds it. The deploy workflow takes each build's base path from it. Without the variable, the build falls back to `https://jburkinshaw.github.io/crossing-map/`, so removing it undoes the move.
- **DNS.** The apex has GitHub's four `A` and four `AAAA` records, and `www` is a `CNAME` to `jburkinshaw.github.io`, which GitHub redirects to the apex. The domain is verified on the owner's GitHub account, so no other account can serve it, and has no wildcard record.
- **Old links.** GitHub answers `jburkinshaw.github.io/crossing-map/` with a 301 to the domain, and the browser keeps the `#` part, so old links to pages and map views still work.
- **Cost.** The domain costs about $12 a year (Porkbun's `.com` price in November 2026), the project's first running cost. Hosting stays free, so the $0 a month at 10,000 visits of design section 11 still holds for the site itself.
