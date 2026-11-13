# Stage 5 review: translations groundwork

This folder holds the first pass at the site's own translations of the Spanish in the novel. It covers the pipeline and data only; there is no UI yet. Nothing here is published until you review it.

## Files

| File | What it is |
| --- | --- |
| `translations-review.csv` | Every Spanish span found, with its incipit, our draft English, confidence, note, speaker, listener, place and guide page. Edit this file. |
| `translation-gaps.csv` | The spans that have no entry in the Campbell guide (the gap list from plan section 8). |
| `road-refs.csv` | Runs of lines judged by hand to be spoken on one route segment (talk on the road). |
| `where-spoken.csv` | Single lines judged by hand: where each was spoken (stop, place, area or segment), or left null, with a reason in our own words. |
| `../../data/translations.json` | The published record, built from the two sources below. Schema: `data/schema/translations.schema.json`. |

Private working files (git-ignored, under `private/translations/`): `spans.json` (each full Spanish span and its context), `guide-entries.json` (the guide's pages and Spanish openings), `drafts/` (the draft translations by batch), `es-search.json` (accent-folded full spans).

Rebuild from the repo root:

```
uv run --project pipeline python -m crossing.translations find    # private text and guide -> private/translations/spans.json
uv run --project pipeline python -m crossing.translations build   # spans + drafts + this CSV -> data/translations.json and the CSVs
uv run --project pipeline python -m crossing.validate
```

`build` keeps your edits: any non-empty cell in `translations-review.csv` wins over the draft. Span ids (`tr-<episode>-<nnn>`) are numbered in reading order within each episode. Do not run `find` again with changed detection settings after you start editing, or the ids can shift.

## Method

1. **Guide.** The Campbell guide PDF was downloaded once to `private/cache/translations/` (not committed). It has a text layer, so no OCR was needed. The parser keeps each entry's page, Part and Spanish opening, and drops the English in brackets. The guide's English is never stored, compared or copied. 438 entries were parsed (Part I 134, II 38, III 138, IV 128).
2. **Spanish in the text.** Each paragraph of the 41 episode files is split into sentences. A trailing English dialogue tag ("he said", "the old man wheezed") is cut off, and the rest is language-identified with lingua (English against Spanish only). A clause counts as Spanish when the model is confident and few of its words are English dictionary words. Consecutive Spanish sentences in one paragraph form one span, even with a dialogue tag between them. Inside English sentences, single Spanish words (and short runs such as "hermanos en armas") are found from the dictionary, the model and the guide's one-word entries. A word that recurs in the narration ("alguacil", "carretero") is glossed once, where it first appears; the `occurrences` column says how often it recurs. A bare "No." is dropped, because it reads the same in English.
3. **Guide matching.** Text is accent- and case-folded. Each guide entry is matched to the best span within 6 pages of its printed page, by rapidfuzz partial ratio of at least 85. Entries of one or two words must appear as whole words. A span can hold several guide entries, because the guide often splits one speech; `guide_page` is the page of the first.
4. **Pages.** The ebook has no print pages. 132 long guide entries that matched with a score of 92 or more became page anchors (offset in the text, guide page). The anchors were kept in order (longest increasing chain), and pages between them are interpolated. Episode start pages come out at Part II 128, Part III 214 and Part IV 333, against the guide's 131, 215 and 342. Treat every `page` as approximate, within about 2 pages where anchors are dense and worse in the gaps the plan lists (for example Part One 51 to 69). The Part IV figure may be early because the guide's first Part IV entry is not on the Part's first page.
5. **Where it was spoken.** `location_ref` is the stop of the same episode whose place name the text gave most recently before the line. If no stop is named, a place first named in that episode (as a stop or in passing) is used. Otherwise it is null. Descriptive stops ("The girl, at a fire in an oak grove") cannot be found by name, so their talk is often null or points to the town named just before. This is a heuristic: check it. Two hand-made files correct it, both read by the same step in the build (`load_hand_refs`). `road-refs.csv` lists runs of lines, judged from the episode's stops and segments, that are spoken while travelling one route segment (talk on the road, plan section 8); a run fills only lines the heuristic left without a place. `where-spoken.csv` lists single lines (`id`, `ref`, `kind`, `why`) and replaces the heuristic. An empty `ref` records a line the text does not place and changes nothing. A segment reference has `location_kind` `road`; every other reference has the kind of its layer (`stop`, `place`, `area`). The build stops if a ref does not exist with the stated kind, is first seen after the line, or is a segment not travelled in the line's episode, or if a line is in both files. A hand edit in `translations-review.csv` still wins over both; a cell that only repeats the heuristic does not count as an edit. See `patterns.md`.
6. **Drafts.** The English is ours. It was drafted from the Spanish and its context, without reference to the guide, in plain and faithful wording. Each line has a confidence and, where useful, a note on northern Mexican or rural usage or on a scan error in the ebook (the ebook has OCR errors such as "to" for "lo"). Speaker and listener are slugs (`billy`, `boyd`, `father`, or a role such as `old-man`), filled in only when the context makes them clear.

## Counts

| Part | Spans found | Skipped as not Spanish | Published entries | Linked to a guide page | Gaps | Spanish-heavy paragraphs (plan heuristic) | Same measure, this run |
| --- | --- | --- | --- | --- | --- | --- | --- |
| I | 211 | 1 | 210 | 123 | 87 | 53 | 101 |
| II | 118 | 4 | 114 | 30 | 84 | 24 | 56 |
| III | 341 | 2 | 339 | 123 | 216 | 99 | 162 |
| IV | 258 | 5 | 253 | 104 | 149 | 56 | 131 |
| Total | 928 | 12 | 916 | 380 | 536 | 232 | 450 |

Of the 928 spans found, 148 are single words or short phrases in English narration (each glossed once), and 780 are lines of Spanish speech.

"Spanish-heavy paragraphs, this run" counts paragraphs where over half the characters are in Spanish sentences. It is about double the plan's heuristic, because McCarthy's dialogue puts each short line in its own paragraph ("Sí.", "Gracias."), and this run counts those. The ratio between the Parts is similar.

Guide entries matched to a span: 391 of 438 (Part I 122 of 134, II 36 of 38, III 125 of 138, IV 108 of 128). Most of the 47 unmatched entries are scan errors in the guide or the ebook, lines the guide abbreviates heavily, or lines that sit just outside the page window. The unmatched list is in the private working files only, because it quotes the novel's Spanish.

Drafts: all 916 published entries have our English. Confidence: 860 high, 66 medium, 2 low (Part I 197, 12, 1; II 102, 11, 1; III 310, 29, 0; IV 239, 14, 0). Most medium ratings are lines where the text does not say who speaks, so the speaker was inferred, or lines with scan errors in the ebook. 760 entries have a speaker.

Where it was spoken, for the 916 published entries:

| | Placed at a stop, place or area | On the road | No place |
| --- | --- | --- | --- |
| Name heuristic only | 661 | 0 | 255 |
| After `road-refs.csv` (previous pass) | 661 | 52 | 203 |
| After `where-spoken.csv` (this pass) | 847 | 67 | 2 |

By kind, the 916 are now 754 `stop`, 93 `place`, 67 `road` and 2 null. Of the 847 placed, 226 were judged by hand in `where-spoken.csv` and 621 still rest on the name heuristic alone.

### This pass: `where-spoken.csv`

Each of the 203 lines with no place was read in context. 201 now have a place and 2 are left null, both in 3-14: a charm he looks at during weeks of searching, and a word said of two hamlets together. Most of the rest are said at one stop:

| Episode | Lines | Where |
| --- | --- | --- |
| 3-09 | 67 | The blind man's house (`j4-blind-man`). 32 lines are inside the tale the wife tells at the table; they take the house too, because the tale's own places are not on the map (see the questions). |
| 4-04 | 56 | Janos (`j7-janos`): the morning after the cantina, in a field at the edge of the town. |
| 3-07 | 19 | Boquilla (`j4-boquilla`, the stop of 3-06), where the one-armed man falls. 3-07 has no stop. |
| 1-10 | 17 | The hacienda (`j2-hacienda`). |
| 3-01 | 10 | The Hacienda de San Diego on arrival (`j4-san-diego`). The previous pass (`patterns.md`) put these at the opera camp on the Madera road; the text has them at San Diego, where the troupe is playing that night. |
| 3-11, 3-13 | 7 | The San Diego ejido during Boyd's recovery. Neither episode has a stop, so these take the place `place-hacienda-de-san-diego`. |
| 3-12 | 6 | Leaving San Diego at dusk (`j5-san-diego`). |
| Others | 19 | One stop each: the heretic's town (2-02), Bacerac (2-08), the river camps (3-02), Las Varas (3-04), Boquilla (3-06), the dry camp (3-08), the doctor's house in Casas Grandes (3-10), Buenaventura (3-14), Berendo (4-03), Namiquipa (4-05), the gypsies' camp (4-07). |

**1-09 corrections.** The heuristic had put 32 lines after the Cabellera passes at the Sierra de la Cabellera stop, because no later place is named until Morelos. The text puts them elsewhere, and `where-spoken.csv` now says so:

- `tr-1-09-064` to `-076` (13 lines): the deputies stop Billy on the gravel bar after he swims the wolf across the Bavispe. Now `j2-colonia-oaxaca`, the river crossing stop.
- `tr-1-09-077` to `-111` (12 lines): the alguacil questions him in the mud-house settlement, and the carretero takes the wolf from there. Now `j2-mud-settlement`.
- `tr-1-09-118` to `-124` (7 lines): he rides out with the pilgrims bound for the fair. Now the road `j2-seg-10` (settlement to Colonia Morelos).

The next 8 lines (`tr-1-09-125` to `-134`) pointed at Colonia Morelos only because the pilgrims had just named it. They are the same walk and the pilgrims' camp in a meadow on the way, so they are on `j2-seg-10` too. Talk on the road is now 67 lines on two segments.

## Guardrails (plan section 3)

- **Incipits only.** Committed files hold at most the first five words of each Spanish span (`es_incipit`, with "…" when cut). `crossing.validate` fails on a longer incipit. For a span of five words or fewer, the incipit is the whole span; for one-word glosses this cannot be avoided.
- **`es_search` is not published.** The plan's record has `es_search` (the accent-folded full span, for the search index). Published in full, it would put the novel's Spanish passages in the repo and the site, which section 3 rules out. It is kept out of `data/translations.json` and the schema forbids it. The folded spans are written to `private/translations/es-search.json` only. The search agent can index `es_incipit` (folded) and our English. Accent-insensitive search on the incipit still finds most lines by their opening.
- **The guide is not copied.** We hold only its page numbers (`guide_page`). Our English was drafted without the guide. Each entry with a `guide_page` can link to the guide with the credit "Campbell's guide: Lt. Jim Campbell, cormacmccarthy.com" (plan section 3).
- **Spoilers.** Each line's `first_seen` is its own episode. `location_ref` never points at a feature first seen later, and validate checks this.

## How guide links work

The guide is one 15-page PDF with no anchors, so a link cannot go to an entry. The UI can link to the PDF (`#page=N` works in most browsers' viewers) with the credit, and say "listed under page P", where P is `guide_page`. The PDF page that holds Vintage page P can be found from the parsed entries; that lookup is not built yet, because the URL and the hosting may change. `guide_page` is the page the guide prints, not our estimate. For Part IV the guide lists pages 353 to 357 after 368. Those entries match lines that this run places on pages 366 to 369, beside the guide's own 366 and 367, so the guide's page numbers there are probably misprints. The links keep the guide's printed page, so a reader finds the entry where the guide puts it.

## What to review

1. **Draft English** in `translations-review.csv`: start with `confidence` low and medium, then the notes. Put `yes` in `reviewed` when a line is done. Ideally a speaker who knows northern Mexican usage reads the whole file (plan section 8).
2. **False positives:** set `skip` to `yes` for anything that is not Spanish. 12 are already marked, mostly proper names said in English. They stay in the CSV but are left out of `translations.json`.
3. **Missed Spanish:** the gap list covers spans we found. Spanish we did not find shows up as an unmatched guide entry (47, listed in the private working files) or not at all. Sentences that mix English and Spanish words fifty-fifty are the likely misses.
4. **`location_ref`:** the 226 hand judgements are in `where-spoken.csv`, each with its reason; change a `ref` there, or write `none` in `translations-review.csv` to clear a line. The 621 heuristic references were not all checked in this pass. While reading context I saw these that look wrong (not changed, because they were outside this pass):
   - 1-10, 26 lines from `tr-1-10-060` on: the wolf in the pit and the ride out. They point at `place-casas-grandes` (8) and `place-colonia-oaxaca` (18), because those names appear in the crowd's description and the dialogue. The pit is in the hacienda's bodega, so most are probably `j2-hacienda`, and the last ones are at the ford on leaving.
   - 3-10, `tr-3-10-010` to about `-021`: still at the doctor's gate in Casas Grandes, but pointing at `j4-san-diego-doctor` (the drive back to San Diego). The rest of 3-10 may be right.
   - 2-01: 24 lines point at `j3-el-tigre`. Some, near the church, may be at Huisiachepic.
   - `j3-colonia-oaxaca` (2-03) says the alguacil's house is at Colonia Oaxaca, but in 1-09 the alguacil questions Billy in the mud-house settlement (`j2-mud-settlement`), the stop after the river crossing. One of the two stops needs a look.
5. **Speaker and listener slugs:** check them against the characters the site will name. People the text has not named yet are given roles, and the drafts were made in seven batches, so the slugs are not fully consistent. For example, `woman` and `girl` each stand for more than one person, and the old man in 1-07 is `old-man`, not a name. A pass to make them consistent is needed before the UI shows speakers.

## Open questions for the owner

1. Is a whole short line acceptable as its "incipit" when the line has five words or fewer? The plan's rule allows an opening phrase. For short lines the opening phrase is the whole line, but each line is still only a few words.
2. Should a recurring word in the narration have one glossary entry (as now) or one entry per Part?
3. Should a run of short lines in one exchange be grouped into one entry ("exchange", plan section 6)? The data now has one entry per line, as the guide does. Grouping would cut the count by about half and make each card more useful.
4. `conversations.geojson` (plan section 6) is not built. Its points could come from `location_ref`. Talk on the road now points at a route segment, and the map draws the 2 km corridor itself (see `patterns.md`).
5. The page model could also fill `pages` in `episodes.json`, which is null now. This was not done here, because that file is out of scope for this stage.
6. Lines inside a tale told in the story (the blind man's wife's tale in 3-09, 32 lines) now point at the place where the tale is told, not at the tale's own places, which are not on the map. Is that what you want, or should they stay null?
7. Two lines in 3-14 stay null: the text does not place them. Should they get the nearest stop of the search (for example Buenaventura), or stay null?
8. The 7 lines in 3-11 and 3-13 point at the place `place-hacienda-de-san-diego`, because neither episode has a stop. Would you rather they took a San Diego stop (for example `j4-san-diego-doctor`, the last one before them)?
