# 0019. Raised over every journey, in archives under 100 MB

Status: accepted (2026-11-13). Extends 0018.
Phase: P1

## Context

Decision 0018 raised the corridor of J1 and J2. Stage 4 has since drawn J3 to J7, and the fine hachure corridor now follows only the stretches ridden or walked (plan 5.2), not bus rides or the reported J6. Built as one archive, Raised over that corridor would be about 105 MB, over the plan's 100 MB per file.

## Decision

- **Area.** `RAISED_JOURNEYS` in `crossing.plan_oblique` names all seven journeys, and the area is the fine corridor: 87 tiles, about 82,000 km². One lowest height covers it all, as in 0018.
- **Strips.** A column of tiles can hold separate stretches of the corridor, so each unbroken run of tiles is its own strip (12 in all). A gap between runs is at least one 40 km tile, far more than the 5 km a ridge can hide, and each strip's DEM still reaches 6 km south of it.
- **Archives.** The strips are tiled in groups, and a group whose archive passes 95 MB is halved and tiled again. The result is `oblique-1.pmtiles` (86 MB) and `oblique-2.pmtiles` (19 MB), listed in `data/raised/archives.json`. The app draws every raised layer once per archive.
- **Story.** `data/raised/` holds every journey; lines are simplified to about 10 m after the shift (0.9 MB in all).

## Alternatives

- **Tiling the zoom-12-only strokes separately.** It keeps one main archive, but the main archive would still be about 120 MB.
- **Fewer zoom levels for strokes.** Smaller, but strokes over-zoomed from zoom 11 would show their 10 m steps at zoom 13.

## Consequences

- The tiles release carries two Raised archives, and more if the corridor grows; `archives.json` must ship with them.
- Bus rides and reported journeys cross bare paper in Raised, as the notice says. Lakes and the Mexico tint stay flat.
- A full build takes about 3.5 minutes.
