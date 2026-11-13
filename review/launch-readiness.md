# Launch readiness: the plan's acceptance criteria (section 12)

Checked overnight on 13 November 2026 against `stage/4-rest-of-book`. The boxes in `docs/plan.md` stay unticked: ticking them is the owner's sign-off.

| Criterion | Status | Evidence |
| --- | --- | --- |
| Every feature has `certainty`, `source`, `source_licence`, `first_seen` | Met | All 1,541 features in places, stops, areas, journeys, mountain_glyphs and vignettes carry all four (a script check); `crossing.validate` enforces them through the schemas. |
| With progress at any episode, nothing later shows anywhere (map, panel, search, translations, vignettes); automated test | Met | `tools/spoiler-leak.mjs` (`npm run spoiler-leak` in tools/) covers story layers, rendered features, markers, panel text, journey options, stepping, search (44 queries per point), place cards and translations, the layer key, glyphs, vignettes and the Raised view, in both themes. No leaks at any point tested. Not yet in CI (see the morning list). |
| Every photo, tile set and dataset has visible attribution where shown and on the Credits page; the MapTiler logo shows on satellite | Mostly met | Each tile archive carries its credit in its metadata and MapLibre shows it; the Credits page lists every source. Two credit wordings are marked TODO on the page (the full Copernicus notice; Natural Earth's line). No photos are shown yet. The MapTiler logo cannot be checked locally (the key refuses localhost); check on the preview. |
| No passage of the novel is in the repo or the built site; Spanish appears only as incipits | In progress | A scan of every tracked file and the built site for runs of eight words from the novel found close paraphrase in 29 seed and review rows (directions, mostly one or two runs each) and about 12 runs in the plan's own journey descriptions. The rows are being reworded and a standing check (`crossing.echo_check` or similar) added. Incipits are at most five words and, since commit acb471b, hold only the speaker's Spanish. |
| GeoJSON downloads validate against the schemas and open in QGIS | Met | `crossing.validate` passes on every file; every GeoJSON and GeoParquet file opens in GDAL (`ogrinfo`), which is what QGIS uses. |
| The literary map works with MapTiler unreachable | Met | Locally MapTiler always refuses (403); the classic map, every view, search and pages work, and the satellite options switch off with a notice. |
| Panel and drawer pass a one-handed phone test and keyboard-only use | Mostly met | 33 of 34 keyboard checks pass (the Compare swipe needs satellite). Open: the drawer handle at full height is out of thumb reach; no keyboard equivalent for hover names; no real screen-reader test. A hands-on phone test is the owner's. |
| $0 a month at 10,000 visits; satellite pauses rather than bills | Met by design | GitHub Pages and release assets are free; MapTiler's free plan pauses at its limits (decision 0005). The tile set is about 400 MB per build; Pages' 1 GB limit counts main and the preview. |

## Open questions in section 12

Settled overnight: translation permission (no request; ticked in the plan). The rest (relief tool, vignette drawing, name and domain, spoiler default, interface language, licences, Reddit thread, portfolio framing, inspiration folder) are the owner's.
