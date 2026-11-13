# Stage 5 review: translations groundwork

This folder holds the first pass at the site's own translations of the Spanish in the novel. It covers the pipeline and data only; there is no UI yet. Nothing here is published until you review it.

## Files

| File | What it is |
| --- | --- |
| `translations-review.csv` | Every Spanish span found, with its incipit, our draft English, confidence, note, speaker, listener, place and guide page. Edit this file. |
| `translation-gaps.csv` | The spans that have no entry in the Campbell guide (the gap list from plan section 8). |
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
5. **Where it was spoken.** `location_ref` is the stop of the same episode whose place name the text gave most recently before the line. If no stop is named, a place first named in that episode (as a stop or in passing) is used. Otherwise it is null. Descriptive stops ("The girl, at a fire in an oak grove") cannot be found by name, so their talk is often null or points to the town named just before. This is a heuristic: check it.
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

Drafts: all 916 published entries have our English. Confidence: 860 high, 66 medium, 2 low (Part I 197, 12, 1; II 102, 11, 1; III 310, 29, 0; IV 239, 14, 0). Most medium ratings are lines where the text does not say who speaks, so the speaker was inferred, or lines with scan errors in the ebook. 760 entries have a speaker and 255 have no `location_ref`.

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
4. **`location_ref`:** most worth checking in 1-09, 2-08, 3-09 and 4-05, where several stops share an episode. Write `none` to clear it.
5. **Speaker and listener slugs:** check them against the characters the site will name. People the text has not named yet are given roles, and the drafts were made in seven batches, so the slugs are not fully consistent. For example, `woman` and `girl` each stand for more than one person, and the old man in 1-07 is `old-man`, not a name. A pass to make them consistent is needed before the UI shows speakers.

## Open questions for the owner

1. Is a whole short line acceptable as its "incipit" when the line has five words or fewer? The plan's rule allows an opening phrase. For short lines the opening phrase is the whole line, but each line is still only a few words.
2. Should a recurring word in the narration have one glossary entry (as now) or one entry per Part?
3. Should a run of short lines in one exchange be grouped into one entry ("exchange", plan section 6)? The data now has one entry per line, as the guide does. Grouping would cut the count by about half and make each card more useful.
4. `conversations.geojson` (plan section 6) is not built. Its points could come from `location_ref`. Talk on the road needs the corridor buffer from section 8, which belongs with the UI work.
5. The page model could also fill `pages` in `episodes.json`, which is null now. This was not done here, because that file is out of scope for this stage.
