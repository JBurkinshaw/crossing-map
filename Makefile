# One entry point for the checks and the build steps in docs/pipeline.md, in that order.
# Every step that reads private/ fails without the author's copy of the book or the source caches.
# Run `make help` for the list.

PY := uv run --project pipeline python -m

.PHONY: help check extract story summits translations relief raised tiles art install-tiles dev

help:
	@grep -E '^[a-z-]+:.*## ' $(MAKEFILE_LIST) | sed -E 's/:.*## /\t/'

check: ## The checks CI runs: lint, tests, schemas, GeoParquet parity
	uv run --project pipeline ruff check
	cd pipeline && uv run pytest -q
	$(PY) crossing.validate
	$(PY) crossing.downloads --check
	cd site && npm run lint && npm test

extract: ## Episodes, mentions and episode texts from the book (needs the epub in private/book/)
	$(PY) crossing.extract

story: ## Episode list, story layers and vignette anchors; run `make raised` after, as validate compares data/raised/
	$(PY) crossing.build_episodes
	$(PY) crossing.build_story
	$(PY) crossing.build_vignettes

summits: ## Peaks, then landforms; landforms must follow every peaks run (needs private/)
	$(PY) crossing.peaks
	$(PY) crossing.landforms

translations: ## Spanish lines and their placement (needs private/)
	uv run --project pipeline --extra translations python -m crossing.translations find
	uv run --project pipeline --extra translations python -m crossing.translations build

relief: ## Hachure strokes for every scale; set QGIS_ENV (hours)
	$(PY) crossing.hachures --scale all

raised: ## The Raised view's archives and data/raised/ (hours)
	$(PY) crossing.plan_oblique

tiles: ## Base, relief and terrain archives into tiles/out/
	$(PY) tiles.build_base
	$(PY) tiles.build_relief
	$(PY) tiles.build_terrain

art: ## Glyph and vignette SVGs, then the sprite (needs spreet)
	$(PY) art.glyphs.make_glyphs
	$(PY) art.vignettes.make_vignettes

install-tiles: ## Copy tiles/out/ into the local site
	$(PY) tiles.install

dev: ## The site's dev server
	cd site && npm run dev
