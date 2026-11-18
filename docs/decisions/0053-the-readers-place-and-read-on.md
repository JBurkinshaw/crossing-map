# 0053. The reader's place in the address and on the device, and "Read on"

Status: accepted (2026-11-17)
Phase: P1

## Context

The site is meant to sit beside the book as a reading companion. It already stored the reader's progress, an episode, in `localStorage`, and on load brought into focus the stop they reached most recently (decision 0034). It did not keep the stop the reader was on. A reader who stepped back two stops and reloaded came back to the episode's last stop. A bookmark kept the camera (`#map=`) but not the stop.

Moving on through the book was also slow. At the last stop reached, Next is disabled, and the only way on was to open "Where are you up to?" and pick the next episode.

## Decision

- **The stop in focus is the reader's place.** It is kept in two places. The address has it as `#stop=<id>` beside MapLibre's `map=`, so a bookmark or a shared link opens at it. `localStorage` (`crossing-map.place`) has it too, so the next visit to the bare address opens there. `site/src/spoiler/place.ts` holds both.
- **On load, the first of these that the reader has reached wins:** the link's stop, the stop saved on this device, then the stop they reached most recently (`resumeStop`). Each is looked up in the story already filtered to the reader's progress, so a link from a reader further on never shows a later stop. It also never moves the reader's progress. On a first visit the link's stop waits until the reader sets their progress, and opens then if they have reached it.
- **Setting progress in the dialog still brings the stop reached most recently into focus**, and that stop becomes the saved place.
- **The address is updated with `history.replaceState`**, as MapLibre does for the camera. Back still leaves the site, and moving through stops does not fill the history. The page router only reacts to `#/` hashes, so `stop=` does not disturb it.
- **"Read on"** shows at the end of the stop section on the stop the reader reached most recently, while there is a next episode: "Finished Part I, episode 9?" over a button "Read on: Part I, episode 10: ‘The hacienda…’". It sets progress to the next episode, with no confirmation, because the button names exactly what it will show and shows one episode only. The map then moves to the stop reached most recently, as any change of progress does. Focus moves to that stop's name, since the button can disappear with the stop it was on. Its block is ruled off and its button styled like the talk-on-the-road block above it, so the stop section keeps one kind of action button.

## Alternatives

- **The address alone.** Bookmarks and shared links work, but a reader who comes back by typing the address, the usual case for a companion, starts over.
- **`localStorage` alone.** Coming back works on one device, but a place cannot be bookmarked, sent to a phone, or shared.
- **`pushState` for each stop**, so Back steps back through stops. It would put dozens of entries in the history, and MapLibre's own camera updates replace the entry, so the two would fight.
- **A stop's journey and sequence in the address (`J2.11`)** in place of its id. It would not show the place's name in the address of a link from a reader further on. But sequences change as stops are added, which would break saved links, and ids are stable. A reader only sees a later stop's id if someone further on sends them a link.
- **Read on to the next stop's episode**, not the next episode. A journey's next stop can be several episodes on (J4 has none from 2-07 to 3-08), so this could show several episodes at once.
- **Read on on the last stop of every journey.** A reader browsing back to J1's end, far behind their progress, would see an offer that has nothing to do with that stop.

## Consequences

- The address names the reader's stop, and with it a place in the book. A link shared by a reader further on shows a later place's id in the address bar, though not on the map or in the panel.
- `tools/spoiler-leak.mjs` reaches every episode with "Read on" and checks that each shows nothing past it. After moving progress back, it opens a link to a later stop with a later place saved, and checks that neither shows (decision 0054).
- `site/src/storage.ts` now holds the try-and-ignore pattern that reading progress, units, folds, and the place each used on their own.
