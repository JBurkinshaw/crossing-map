# Contributing

Corrections are the most useful thing a reader can send. This project is run by one person, so changes go through issues first.

## Send a correction

Open an [issue](https://github.com/JBurkinshaw/crossing-map/issues). Every place card and translation on the site has a link that opens one with the details filled in. A good correction gives:

- **What:** the feature's id (shown in the prefilled issue) or its name and journey.
- **Where it should be,** if it is a place: coordinates, or a link to a map.
- **Why:** a page of the novel (Vintage paperback), a source with a link, or local knowledge.
- **The episode** in which the book first names it, if you know it, so spoiler mode can date it.

Accepted corrections are credited in [`docs/CHANGELOG.md`](docs/CHANGELOG.md), unless you ask otherwise.

**Never paste text from the novel** into an issue, a commit, or a file, not even a sentence. Cite the page and say it in your own words. The site republishes no text from the book, and the repository must not hold any.

## What never enters the repository

- **The novel**, in any form: text, extracted passages, or offsets that would rebuild it. The owner's copy stays in `private/book/`.
- **Second sources' words:** Bell's dissertation, Campbell's English translations, and readers' notes. We cite and paraphrase.
- **Reference images** from the Cartographers' Guild, the Rumsey collection, or anywhere else we do not own. Indexes of titles and links are in `docs/inspiration/`; the images stay in `private/inspiration/`.
- **Built tiles.** PMTiles archives are GitHub Release assets (decision 0004).

`private/` is git-ignored, and CI fails if any file under it is tracked. It is an ordinary folder on the owner's disk: not encrypted, and not backed up by the repository.

## Checks to run before a commit

From the repo root, `make check` runs the first four; the rest need the private text or a running site.

```bash
(cd site && npm run lint && npm test)
uv run --project pipeline ruff check
(cd pipeline && uv run pytest)
uv run --project pipeline python -m crossing.validate
uv run --project pipeline python -m crossing.echo_check   # needs the private text; skips without it
(cd tools && node spoiler-leak.mjs http://localhost:5185/)   # a VITE_DEBUG=1 build served by vite preview
```

`crossing.echo_check` reports any run of eight words shared with the novel. A match is a prompt to reword, not proof of copying: place names and stock phrases are shared by nature.

The spoiler-leak test checks ten reading positions locally (about 100 seconds each). CI runs four; set `SPOILER_POINTS` to choose others. New screenshots under `review/` are ignored by git: put them in `private/review/` or attach them to a release.

## Decisions and documentation

- A technical or judgement call that others would ask about gets a record in [`docs/decisions/`](docs/decisions/README.md). The site publishes these records.
- Open work and pending decisions go in [`docs/roadmap.md`](docs/roadmap.md), and reader-visible changes in the changelog.
- Measurements (distances, areas, bearings) are computed by a script in `pipeline/measure/` with open-source tools, stating the ellipsoid or projection and the source of every coordinate. Estimates are labelled as estimates.
