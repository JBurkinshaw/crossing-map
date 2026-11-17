# Licence and attribution checklist (2026-11-16)

One row per source: what its terms ask, where the site and the data meet them, and what is left. [`docs/licensing.md`](../../docs/licensing.md) explains the reasoning. Tick a row when you've checked it.

"Credits" is the Credits page. "Map" is the map's credits list. "Data" is `data/README.md` and each feature's `source_licence`.

## Sources in the data and tiles

| ✓ | Source | Licence | It asks for | Met by | Left to do |
| --- | --- | --- | --- | --- | --- |
| [ ] | Copernicus DEM GLO-30 | Copernicus DEM licence | The "produced using…" notice, the disclaimer, and the same terms downstream | Credits (full notice and disclaimer), Data (notice), each archive's credit on the map (short form) | None (`data/LICENSE` names it) |
| [ ] | GeoNames | CC BY 4.0 | Credit, licence link, changes noted | Credits, Data, `water_places` credit on the map | None found |
| [ ] | GMBA Mountain Inventory v2 | CC BY 4.0 | The same | Credits, Data | Re-read GMBA's own licence page |
| [ ] | CEC Land Cover 2020 | CC BY 4.0 | The same | Credits (now says "transformed"), Data, `landcover.pmtiles` credit | Re-read the CEC's licence page |
| [ ] | Global Dam Watch and GRanD | CC BY 4.0 | The same | Credits ("transformed") | Only its dates are used, nothing is drawn. Re-read its page |
| [ ] | INEGI Red Hidrográfica 1:50k | INEGI free-use terms | "Fuente: INEGI", product name and date, changes noted, no implied endorsement | Credits (now says "transformed"), Data, `base.pmtiles` credit | Add the edition date to the "Fuente" line if INEGI gives one |
| [ ] | INEGI Red Nacional de Caminos 2024 | INEGI free-use terms | The same | Credits ("transformed"), 13 features' `source_licence` | None found |
| [ ] | USGS GNIS and NHD, Census TIGER | Public domain | Nothing, credit is a courtesy | Credits, Data | None |
| [ ] | Natural Earth | Public domain | Nothing | Credits | None |
| [ ] | Wikidata | CC0 | Nothing | Credits, 5 features | None |
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
| [ ] | Code | MIT (`LICENSE`) | Confirm |
| [ ] | Hachure generator | GPL-3.0, with Huffman's credit and the change list (`pipeline/relief/hachures/`) | None |
| [ ] | Data and notes | CC BY 4.0 (`data/LICENSE`, decision 0045) | None |
