# What is outstanding

Compiled on 13 November 2026 from the plan, every review packet, the decision records, the open questions, the overnight morning list and the code. The plan (`docs/plan.md`) stays the source of truth: this is an index. The tags say who moves each item:

- **[you]**: an action only the owner can take
- **[decide]**: a decision for the owner
- **[build]**: work Claude can do once asked
- **[research]**: needs evidence that is not yet to hand

## 1. To get the site out for scrutiny

1. **[you]** Publish `tiles-v6`. It holds the new base archive (Mexico's rivers from INEGI) and the six unchanged archives. Then push `stage/4-rest-of-book`.
2. **[you]** **Merge into main.** `main` and the public root still show stage 2 with `tiles-v2`, and stages 3 and 4 were never merged. Either merge `stage/4-rest-of-book` to main through a PR, or launch on `/preview/`.
3. **[you]** Check the preview, which localhost cannot test:
   - the MapTiler logo, Satellite, Topo, Compare and Land colour (the key's allowed domains)
   - a one-handed phone test
4. **[you]** Sign off the stage 4 place checklists (`review/stage-4/batch-a/checklist.md` and `batch-b/checklist.md`) and tick the acceptance criteria in plan section 11.
5. **[you]** Send the permission message to Joe Hazelton. A courtesy note to James Bell is optional.
6. **[decide]** How readers discuss. Cusdis is archived (July 2026), so it is out. The options are Giscus (needs a GitHub account to post), Hyvor Talk (guest comments, about €50 a year), or a Tally form beside Giscus. The GitHub issue link stays for corrections.
7. **[you]** Soft launch to a few readers. Then post on r/cormacmccarthy (draft in `private/launch/reddit-post.md`, which needs the link and two screenshots), and reply in the 2024 Gaia-map thread.

## 2. Stages not finished

- **Stage 1.**
  - Inferred areas are still circles, waiting for the QGIS redraw in decision 0008.
  - The episode summaries are drafts for you to edit.
- **Stage 2.**
  - Rivers (`tiles-v7`): where INEGI's network breaks, a traced river still falls back to Natural Earth's straight line for a stretch, as on the Río Batepito above Colonia Morelos (7.8 km). `tiles/check_rivers.py` (uncommitted, not yet run to the end) would measure every river against the valley floor and list these breaks.
  - 60 fps on a mid-range phone is not measured.
  - The state names in IM Fell small capitals are not drawn.
  - The Cloverdale Creek road leg is not snapped to a road.
- **Stage 3.**
  - The landform weights need tuning.
  - The hand-drawn mountain glyphs are not done; the generated set stands in.
  - Full-region relief is not decided (section 3).
- **Stage 4.**
  - The checklists above are unsigned.
  - The Animas Valley and La Babícora regions are drafts from the DEM.
  - Most Mexican legs are schematic curves, because INEGI roads were not tried.
- **Stage 5.**
  - The 916 translation drafts are unreviewed. Decided 13 November 2026: crowd review, through a link on each line.
  - Speaker names are inconsistent.
  - `conversations.geojson` is not built.
  - `episodes.json` has no page ranges.
  - The guide links have no deep page link.
- **Stage 6.**
  - No photos are picked; the photo pipeline after the picks is not built.
  - The vignette art is placeholder.
  - The "measured in CI" numbers on How it's built are not measured.
  - The accessibility leftovers are open (section 4).
- **Stage 7.**
  - Judgement calls 2 to 17 in `review/stage-7/README.md` are open. Item 8, De Baca County, was applied on 13 November.
  - Not built: the `leads` field, the `bell-2000` and `reddit-gaia` source ids, and "Also placed by" on cards.
  - Not done: maxZoom 15 for street-level places.
- **Stage 8.** Section 1 above, then the stage 7 calls, street-level places, the declutter, research-based vignettes and analytics, each as demand shows.

## 3. Decisions waiting on you

- **Plan section 12.**
  - the relief tool (Eduard)
  - who draws the vignettes
  - the name and domain
  - the spoiler default
  - the interface language
  - licences
  - portfolio framing
- **Translations** (`review/stage-5/README.md`).
  - short lines as their own incipit
  - grouping exchanges
  - glossary scope
  - `conversations.geojson`
  - page ranges
  - placing the 3-09 tale's lines and five other small location questions
  - the misprinted guide pages
  - the spot-check list
- **Spoiler mode.**
  - Is it fine that almost every glyph is dated 1-01?
  - 21 reasoning texts that cite later episodes: rewrite them, or keep the notice?
  - Should "Show everything" confirm every time, as built, or once, as plan 9 says?
- **Stage 4 questions.**
  - the J3 sierra loop
  - the J4 loop back to Las Varas
  - Bachíniva in J6
  - the Ash Wednesday date
  - the Soto Máynez and Santa Ana label overlap
  - corrections to plan 2.2
- **Stage 7 calls 2 to 17**, which the app now lists as open questions.
- **Vignettes.**
  - the she-wolf's position
  - an obelisk leader
  - leader zoom
  - size
  - a GeoParquet copy
  - the next picks
- **Photos.** Aerial views, linking places without Wikidata ids, and the picks themselves.
- **The drawer.** Open it at peek or half height? What counts as "far" for off-map arrows?
- **Relief.**
  - Full-region relief and Raised, about 710 MB: R2, the preview only, or a thinner treatment?
  - Coarse relief and contours over the whole box?
  - The corridor edge.
  - Thinning pass labels.
  - Glyph thresholds.
  - Raised details.
  - The name of "Land colour".
- **CI.** The spoiler-leak test, bundle size and Lighthouse in the deploy workflow.
- **Analytics.** Cookie-free (GoatCounter or Cloudflare) or Google.

## 4. Build work, by size

- **Small:** done on 13 November 2026 (Bell and Hazelton in Further reading, Veracruz, the vignettes GeoParquet file, the "measured in CI" rows removed, Dependabot, `docs/CHANGELOG.md`, the README).
- **Medium:**
  - the stage 7 data model and card lines
  - the stage 7 moves once decided
  - the photo pipeline
  - the spoiler-leak test in CI
  - the speaker-name pass
  - guide page links
  - `conversations.geojson` and episode page ranges
  - off-map arrows
  - drawer thumb reach and swipe-down
  - a keyboard equivalent for hover names
  - a screen-reader test
  - state labels
  - the combined Soto Máynez label
  - the corridor-edge fade
  - the QGIS redraw of the regions and areas
- **Large:**
  - street-level places (lookups, maxZoom 15)
  - shipping full-region relief and Raised (hosting)
  - real vignette art
  - hand-drawn glyphs
  - translation review by a speaker
  - road snaps for the Mexican legs

## 5. Phase 2 backlog (plan section 11)

- land-cover marks
- Cloudflare R2
- Blender or Eduard relief
- least-cost routes
- Rumsey overlays
- story mode
- a Spanish interface
- illustrator vignettes
- speaker-reviewed translations
- a paid MapTiler month
- analytics
- a feedback form beyond the issue link
- alternative readings drawn on the map, with discussion or votes
- "What Billy saw" panoramas
- creeks
- block diagrams
- the general declutter
- the corridor edge
- research-based vignettes with context labels
- the Trail of Blood Meridian map as a style reference

## 6. Stale or contradictory documents

Fixed on 13 November 2026: the plan (launch, 5.4, 2.2, stage 7, the "Numbers" on How it's built, the five 8-word runs), decisions 0009 and 0016, `TODO-prerequisites.md`, `private/follow-ups.md`, `docs/open-questions.md`, launch readiness, and dated notes on the stage 2, 3, 5 and 6 packets. The 16 agent worktrees under `.claude/worktrees/` remain: each has uncommitted files, so they need a look before removal.
