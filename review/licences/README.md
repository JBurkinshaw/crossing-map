# Licence and attribution checklist (2026-11-16)

One row per source: what its terms ask, where the site and the data meet them, and what is left. [`docs/licensing.md`](../../docs/licensing.md) explains the reasoning. Tick a row when you've checked it.

"Credits" is the Credits page. "Map" is the map's credits list. "Data" is `data/README.md` and each feature's `source_licence`.

## Sources in the data and tiles

| ✓ | Source | Licence | It asks for | Met by | Left to do |
| --- | --- | --- | --- | --- | --- |
| [ ] | Copernicus DEM GLO-30 | Copernicus DEM licence | The "produced using…" notice, the disclaimer, and the same terms downstream | Credits (full notice and disclaimer), Data (notice), each archive's credit on the map (short form) | None (`data/LICENSE` names it) |
| [ ] | GeoNames | CC BY 4.0 | Credit, licence link, changes noted | Credits, Data, `water_places` credit on the map | None found |
| [ ] | GMBA Mountain Inventory v2 | CC BY 4.0 | The same | Credits, Data | None. Re-read 2026-11-18: CC BY 4.0, holder GMBA, in GMBA's `LICENSE` on GitHub (earthenv.org refuses automated reads) |
| [ ] | CEC Land Cover 2020 | CC BY 4.0 | The same | Credits (now says "transformed"), Data, `landcover.pmtiles` credit | None. Re-read 2026-11-18: CC BY 4.0 for data the CEC authored, in the terms of use shipped with the download. The credit is the CEC's own citation |
| [ ] | Global Dam Watch and GRanD | CC BY 4.0 | The same | Credits ("transformed") | None. Re-read 2026-11-18: CC BY 4.0 (technical documentation, section 4.1, and the figshare record). It asks for a citation of Lehner et al. (2024) and a link to globaldamwatch.org, both now in the credit, and asks users not to republish the whole database in its original format, which the site doesn't do |
| [ ] | INEGI Red Hidrográfica 1:50k | INEGI free-use terms | "Fuente: INEGI", product name and date, changes noted, no implied endorsement | Credits (now says "transformed"), Data, `base.pmtiles` credit | Credits and Data now give the date, "agosto de 2010", from INEGI's technical document in the download. The credit inside `base.pmtiles` and the Oblique archives (`tiles/build_base.py`, `crossing.plan_oblique`) picks it up at their next build |
| [ ] | INEGI Red Nacional de Caminos 2024 | INEGI free-use terms | The same | Credits ("transformed"), 13 features' `source_licence` | None found |
| [ ] | USGS GNIS and NHD, Census TIGER | Public domain | Nothing, credit is a courtesy | Credits, Data | None |
| [ ] | Natural Earth | Public domain | Nothing | Credits | None |
| [ ] | Wikidata | CC0 | Nothing | Credits, 5 features | None |
| [ ] | Wikimedia Commons photos (75 picks, decision 0067) | Each photo's own: public domain, CC0, CC BY 2.0 to 4.0, CC BY-SA 2.0 to 4.0 | Title, author, source and licence (TASL) with links, near the photo. BY-SA photos stay BY-SA. Peter Potrowl asks for "© Peter Potrowl" | The TASL line under each photo, Credits (by place, with the date taken), `data/photos.json`, `data/LICENSE` and Data (not part of the CC BY grant) | Check the hand-set authors in `pipeline/seeds/photo-text.csv` against each file page. Public domain files show no licence link, since Commons gives none |
| [ ] | AWS Terrain Tiles (USGS, INEGI in this region) | Public domain, and INEGI's terms | INEGI credit | Credits, `terrain.pmtiles` credit | None found |

## Sources used, not republished

| ✓ | Source | Terms | Met by | Left to do |
| --- | --- | --- | --- | --- |
| [ ] | Joe Hazelton's Gaia GPS map | Permission with basic credit (given 2026-11-16) | Credits ("with the author's permission"), About, Open questions | Ask him before copying any of his pins into the data. Only comparisons are published now |
| [ ] | James Luther Bell, dissertation | In copyright | Facts cited by page, no text copied | Keep the stage 7 item 16 paraphrases short and cited |
| [ ] | Campbell's guide to the Spanish | In copyright | Linked, not copied | None |
| [ ] | Cormac McCarthy, *The Crossing* | In copyright | No passage reproduced (`crossing.echo_check`), and incipits are a few words | None (`data/LICENSE` excludes the quotations) |
| [ ] | Brown, Biotic Communities, and Jenny and Patterson | Cited methods and facts | Credits | None |
| [ ] | Rumsey, Cartographers' Guild, Reddit references | Links only | Credits | None |

## Shown at runtime

| ✓ | Source | Terms | Met by | Left to do |
| --- | --- | --- | --- | --- |
| [ ] | MapTiler (Satellite, Topo) | Free plan: logo and credit visible, non-commercial | Logo and credits in the map's own controls (decision 0043), Credits | Check on the preview, and decide whether a portfolio link on How it’s built is still non-commercial |
| [ ] | OpenStreetMap, in MapTiler's maps | ODbL: "© OpenStreetMap contributors" | MapTiler's credit on the map, Credits | Not in the downloads. Keep it that way |
| [ ] | IM Fell types | SIL Open Font License 1.1 | Credits | None |

## This project's own licences

| ✓ | Item | Now | Left to do |
| --- | --- | --- | --- |
| [ ] | Code | MIT (`LICENSE`) | None. Confirmed by the owner on 2026-11-18 |
| [ ] | Hachure generator | GPL-3.0, with Huffman's credit and the change list (`pipeline/relief/hachures/`) | None |
| [ ] | Data and notes | CC BY 4.0 (`data/LICENSE`, decision 0045) | None |
