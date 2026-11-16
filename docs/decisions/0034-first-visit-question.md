# 0034. Ask on the first visit, then where the reader is up to

Status: accepted (2026-11-16). Owner's decision on the roadmap's "Spoiler default" item.
Phase: P1

## Context

Spoiler mode was on until the reader set their progress (design section 9). A first visit opened two dialogs in a row: the introduction, then "How far have you read?", with a slider of 41 steps, one per episode. Most visitors have either finished the book or not started, and the slider made both answer a fine-grained question. The slider was also hard to use: 41 steps in about 430 px gave each step about 10 px, and its label showed only the episode's opening words, which a reader must match against the book.

The roadmap asked whether to keep spoiler mode on until set, or to ask on the first visit only, and whether "Show everything" should confirm every time.

## Decision

- **One dialog, two steps.** Step 1 is the introduction, with one line on how to use the map ("Press Next to follow a journey stop by stop, or tap anything on the map"). It ends with "Have you finished *The Crossing*?" and two full-width answers: "Yes – show me everything" and "Not yet – hide what's ahead". Focus starts on "Not yet", so pressing Enter straight away keeps spoilers hidden.
- **"Yes" does not confirm.** It answers a direct question about the whole book. "Show everything" from the badge still asks for confirmation, as a reader part way through could press it by mistake.
- **Step 2, "Where are you up to?",** lists "I haven't started" and the 41 episodes by their opening words, grouped by Part. Opening words match every edition, as each episode starts with words in small capitals. The list is a native `<select>` with an `<optgroup>` per Part. A radio list in a scroll box would show more at once, but the select is one control to tab to, the arrow keys and type-ahead work without code, and phones show their own full-screen picker, which is easier with one hand than a scroll box inside a dialog.
- **Two shortcuts** under the list set it. A percentage, for ebook readers, finds the episode holding that point of the book, weighted by each episode's `words` in `episodes.json`. An ebook's percentage also counts its front and back matter, so near an episode's edge it can be one episode out; the list shows the result, and the reader can correct it. A page of the Vintage paperback finds the last episode starting on or before it. The page field shows only when every episode has `pages`, which is null today.
- **The episode chosen is the one being read,** and the map shows it in full, as the slider did. A summary shows only for episodes up to the stored progress.
- **The dialog opens by itself until the reader answers.** Closing it with Escape leaves spoilers hidden and "Not set" on the badge, and it asks again on the next visit. The separate "introduction seen" flag is gone: an answer is the only thing remembered.
- **The badge says what is hidden:** "Showing everything", "Hiding what's after Part I, episode 5: In the woods", "Hiding the whole book", or "Not set". It opens step 2; the panel's Introduction link and the About page open step 1.
- **The map opens where the reader is.** When progress is set to an episode, on load or on a change, the journey with the latest stop at or before that episode comes into focus at its last such stop, and the map flies there. If two journeys share that episode, a journey told first-hand wins over a reported one (J6), then the journey that started later, as the story has moved on to it (J2 takes over from J1 in 1-08). A `#map=` link keeps its view. "Finished" and "not started" open at the start, as before.

## Alternatives

- **Keep spoiler mode on until set, with no question.** First-time visitors who have finished the book had to find the badge and confirm "Show everything" to see the map they came for.
- **Ask on the first visit only and never again.** A visitor who closed the dialog without answering would not be asked again, and would see "Not set" with no prompt.
- **Keep the slider and add Part ticks.** Still 41 small steps, and a phone slider needs a steady thumb.
- **Pages only.** Readers of other editions and ebooks have no Vintage page numbers.

## Consequences

Most readers answer in one tap. Readers part way through choose from words they can see on the page in front of them. The "I've finished it" choice of the old first-visit dialog is now the "Yes" answer. The `crossing-map.introduction-seen` key in `localStorage` is no longer read. The spoiler-leak test (`tools/spoiler-leak.mjs`) drives the new dialog: it answers "Not yet" on first visits, and checks that the list and the percentage shortcut summarise no later episode.
