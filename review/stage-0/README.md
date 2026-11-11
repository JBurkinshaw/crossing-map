# Stage 0 review packet: foundations

## What was built

- The repo layout from the plan, section 11, with MIT for code and CC BY 4.0 for `data/`.
- A Vite, React 19, and TypeScript app in `site/` showing an empty literary map: paper, a 1-degree graticule, and the story box, all from a small PMTiles archive.
- `.github/workflows/deploy.yml`: checks that nothing under `private/` is tracked, validates `data/` against the schema, then deploys `main` at the root and the newest `stage/*` branch at `/preview/`.
- Tiles as GitHub Release assets (`tiles-v0`), downloaded at build time (decision 0004).
- The shared feature schema, `data/schema/story-layer.schema.json`, and its validator, `pipeline/src/crossing/validate.py`.
- Decision records 0001–0009 in `docs/decisions/`.
- `pipeline/measure/distances.py`, which reproduces the distances in the plan.
- `tools/review-packet.mjs`, which takes these screenshots.

## What to look at

1. Open the preview on your phone: https://jburkinshaw.github.io/crossing-map/preview/
2. Pinch and pan. The grid should stay crisp at every zoom.
3. Look at `screenshots/`. Every named view looks the same at this stage, apart from the zoom; later stages fill them in.

## Checks

- Console errors and failed requests during the screenshot run against the live preview: none (`screenshots/problems.txt`).
- Data validation: 0 files, nothing published yet.
- Bundle: 1.36 MB of JavaScript (380 kB gzipped), almost all MapLibre, plus a 520 kB worker.

## Questions for you

None block stage 1. One for later: the bundle is large for a first load on a phone. Splitting MapLibre into its own chunk would make no difference to the total, so I left it.

## Left for later

- The MapTiler key (see `TODO-prerequisites.md`). Stage 1 builds satellite with an "unavailable" state until the key exists.
- Self-hosted IM Fell fonts arrive with the literary styling in stage 2. The title uses a fallback serif until then.

## Live checks (11 November 2026)

- GitHub Pages answers PMTiles range requests: `curl -r 0-99` on `preview/tiles/test.pmtiles` returns `206`, `content-range: bytes 0-99/15598`, and `access-control-allow-origin: *`. Decision 0003 stands.
- The MapLibre worker (`assets/maplibre-gl-worker-*.mjs`) is served as `text/javascript`, so the module worker loads.
- `main` serves a placeholder at the root until this stage merges.
