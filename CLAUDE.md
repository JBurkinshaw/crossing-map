# Working on this repository

Read [`CONTRIBUTING.md`](CONTRIBUTING.md) first: its rules on the novel's text and `private/` apply to every change.

- [`docs/design.md`](docs/design.md) says how the site should work; [`docs/roadmap.md`](docs/roadmap.md) holds open work and the owner's pending decisions. Stay inside them. If a step looks like Phase 2 work, say so and ask.
- Never read anything from `private/` into a commit, fixture, test, or log.
- Ask before any network batch (Wikidata, Commons, GNIS, INEGI downloads) and give the request count. Cache every answer under `private/cache/` so reruns make none. Single lookups of a few requests may go ahead and are logged.
- Compute measurements with pyproj, GDAL, or shapely in a script under `pipeline/measure/`, stating the ellipsoid or projection and the coordinates' source.
- Record every judgement call (which Sierra de la Madera, a horse's speed, a glyph's shape) and every technical choice in `docs/decisions/`, because the site publishes them.
- For style work, read `docs/inspiration/` and `private/inspiration/` first, and name the reference each choice follows.
- Prefer the simplest thing that meets the acceptance criteria in `docs/design.md`, section 11.
