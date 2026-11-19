# 0071. Local history notes on a card

Status: accepted (2026-11-19)
Phase: P1

## Context

Stage 7 item 16 (`review/stage-7/README.md`) proposes short notes of local history from James Luther Bell's dissertation (2000): the dates of Cloverdale's store, post office and school, where Clanton Draw's name comes from, the Hashknife outfit, and others. Each note would be paraphrased, cited by page, and checked for spoilers at its feature's `first_seen`. The notes add context to a place or stop, but they say nothing about where the map puts it, so they do not belong with the second-source leads (decision 0065) or the reasoning under "How this was placed".

## Decision

- **A new hand-written seed, `pipeline/seeds/history.csv`,** with one row per note: the `feature` (a place, stop or area id), the `note` (one or two sentences in this site's own words), the `source` (a source id, for now always `bell-2000`), the `page` or pages it cites, and `show_from`, the episode the note shows from. `show_from` is never earlier than the feature's `first_seen`, and is later where the note would tell of a later episode.
- **`crossing.build_story` adds a `history` array** to each feature the seed names. Each entry gives the note, source, page and `first_seen` (from `show_from`). The build stops on a feature or source it does not know, and on a note shown before its feature. Unlike a lead, an area does not take its stop's notes: a note goes only on the feature it names.
- **`crossing.validate` checks** the notes as it checks the leads' notes: no em dash or semicolon, and no `first_seen` before the feature's. The schema requires all four fields and allows `bell-2000` as the only source for now. The GeoParquet copies type the column from the schema, as a list of records.
- **The card shows each note** as a "Local history" line on the place and stop card, below the card's note, in the faint meta style of the second-source lines (decision 0065), with its citation: "(Bell 2000, p. 61)", linked to the dissertation. The spoiler filter drops a note whose `first_seen` is past the reader's progress, as it does for a dated lead, and the data half of the spoiler-leak test (decision 0054) checks both its date and that it names no place not yet met.
- **The seed ships with its header only.** The 24 drafted notes wait in the private review folder for the owner's review, together, as item 16 recommends.

## Alternatives

- **Append each note to the feature's `reasoning`.** No new field, but it mixes history into the case for where the map puts the feature, and the reasoning can be hidden whole when it cites a later episode, where a note has its own date.
- **Add the notes to `leads.csv`.** A lead is about placement, and there is one Bell lead per feature, so a feature with two notes, or a note on a feature Bell does not place, would not fit.

## Consequences

- The data gains an optional `history` column on places, stops and areas, empty until the owner approves the first notes.
- When the first notes ship, the Bell row of the sources table in `data/README.md` should name `history` as well as `leads`.
- A note's page is a page of the dissertation. Where one gives a range, the card writes "pp.".
