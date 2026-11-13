# 0010. Dating features by episode

Status: accepted (2026-11-11)
Phase: P1

## Context

The spoiler filter hides every feature whose `first_seen` episode is later than the reader's progress. A `first_seen` that is too early spoils; one that is too late only delays.

## Decision

`pipeline/src/crossing/extract.py` reads the author's private copy of the novel. It splits the text into episodes at McCarthy's capitalised scene openings, then records the earliest episode in which each place name appears. It writes nothing of the text to the repo.

- A **place** is dated by its first mention, under any name the book uses for it. The `text_names` column of the seeds holds the book's own spellings, such as Cajon Bonita.
- A short name also matches longer names that contain it: "Animas" matches the Animas Range, and "Cloverdale" matches Cloverdale Creek. So the earliest matches for a short name are read, and the date is set in the seeds by hand. Animas the town first appears in 1-07, not 1-01.
- A **stop** is dated by the episode in which the event at that stop happens, found by reading the episode.
- When the episode is uncertain, take the later one.
- A stop's name must not reveal what the book has not yet revealed. The Part I river crossing is named "the river crossing" until 1-10, the episode in which Colonia de Oaxaca is named.

## Alternatives

- Guessing from summaries: it misses names the summaries leave out. Searching the text needs care too: a first search dated Ascensión and De Baca County to Part IV, missing a variant spelling (Ascención, 1-09) and a passing mention (De Baca, 1-08), which Bell 2000 caught in stage 7.
- Dating every feature to the start of its Part: safe for the filter, but useless for step-by-step reading.

## Consequences

The book has 41 episodes, not 40. The extraction must run on the author's machine; CI checks only the published results.
