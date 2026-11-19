# 0065. Second sources as leads on a feature

Status: accepted (2026-11-18)
Phase: P1

## Context

Stage 7 compared every place with two second sources: James Luther Bell's dissertation (2000) and Joe Hazelton's Gaia GPS map of the novel, found through Reddit (`review/stage-7/README.md`). Some of their points agree with ours, and for a few the two readings are far apart. Until now the agreement or disagreement was only a sentence in a feature's reasoning, where it could not be counted, filtered or shown in a fixed place.

The two sources have different terms (`docs/licensing.md`). Bell is in copyright: his facts may be used and cited by page, but not his text. Hazelton gave permission with credit, which is not a licence, so his pins cannot be republished under CC BY. Whatever records them must state a fact in words and never carry a coordinate.

## Decision

- **Two source ids:** `bell-2000` and `reddit-gaia`. Each has its terms in `crossing.build_story`'s licence table, its credit line in the schema and in `data/README.md`, and its full entry on the Credits page, which already credited both.
- **An optional `leads` array** on places, stops and areas. Each lead gives its `source` and a `relation`, `agrees` or `differs`. It may add a Bell `page`, the `distance_km` between their point and ours (whole kilometres: a fact about the two points, not a position), a short `note` in this site's words, and a `first_seen` where the lead itself would tell of a later episode. Without one it shows with its feature.
- **The seeds hold them,** in `pipeline/seeds/leads.csv`, one row per feature and source. `crossing.build_story` adds them to the places and stops, and an area carries its stop's leads, as it carries its reasoning.
- **`crossing.validate` checks** that a lead's source and relation are known (through the schema), that each source leads once per feature, that only Bell's leads give a page, that no note holds a coordinate, and that no lead is dated before its feature. The spoiler filter drops leads dated after the reader's progress, and the data half of the spoiler-leak test (decision 0054) checks both their dates and that their notes name no place not yet met.
- **The card shows them** inside "How this was placed", above the source line, in the same faint style: "Also placed by" with each agreeing source (Bell with his page where the lead has one), and "Readers disagree:" with each differing source and how far away it puts the feature, in the reader's units. Each source links to the dissertation or to the Reddit thread, as design section 3 asks.
- **The first leads are the settled facts of the stage 7 review only.** These are Hazelton's pins within 0.6 km for Divisaderos, Flores Magón, Ignacio Zaragoza and La Norteña, Bell for Guzmán, and Bell's map of Hidalgo County (Figure 3.2) for Cloverdale, San Luis Pass, Black Point, the Guadalupe Mountains and Hermanas. The disagreements of more than 10 km are Álamo, Las Ramadas, La Boquilla, the Peloncillo Mountains, Fort Bliss, Santa Rita and the Sierra del Nido. The Sierra de la Madera, already decided (keep ours), is the eighth. A stop that stands at the place itself carries the place's leads too. A stop that stands for something else on the same pin, such as the Parham house on the Cloverdale point, does not. No point moved, and no `certainty` changed: the owner's pending calls in the review (items 2 to 7, 9 to 14, 16 and 17) are left as they are.

## Alternatives

- **The agreement in the reasoning text only, as before.** It cannot be listed or checked, and a data user would have to read every reasoning to find it.
- **Their coordinates beside ours.** It would show the disagreement on the map, but it would republish Hazelton's pins, which his permission does not cover, and positions read off Bell's figures.
- **One `second_sources` string per feature.** Simpler, but it could not say which way each source points, and the card could not group them.

## Consequences

- The GeoParquet copies gain a `leads` column, a list of records, typed from the schema.
- Bell's page numbers are not yet in the leads. The pages are in the private findings, so the owner adds them to `leads.csv` when citing each one.
- Where the owner later settles an item of the review, its lead is one row in `leads.csv`: item 17, for example, can then cite its leads when it raises the confidence.
- The Sierra del Nido's lead has no distance. The review records Hazelton's pin there as a village of that name, not measured.
