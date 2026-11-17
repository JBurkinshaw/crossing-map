# 0044. Reader feedback through a Tally form, discussion on Reddit

Status: accepted (2026-11-16). Amends 0020 (how a reader sends a correction).
Phase: P1

## Context

Corrections and better translations went to a prefilled GitHub issue, from a link on each card and each translated line. Posting one needs a GitHub account, which few of the novel's readers have, and the owner did not want readers sent to GitHub. The roadmap also asked how readers discuss the map: Cusdis was archived in July 2026, Giscus needs a GitHub account and Hyvor Talk costs about €50 a year.

## Decision

- **Suggestions go to one Tally form** (free plan), opened in a new tab. Readers need no account. The link fills the form's hidden fields, so each suggestion names what it is about:
  - a card's "Suggest a correction": `kind=correction`, `feature` (the id), `name`
  - a translated line's "Suggest a better translation": `kind=translation`, `line` (the id), `episode`
  - the Open questions page's "Suggest a correction or a new reading": `kind=general`.
- The form asks "What should change, and why?", a source (a page of the book, a map), a name for credit, and an email, the last two optional. Tally emails the owner each submission, and accepted ones are credited in the changelog.
- The form's id is one constant, `FEEDBACK_FORM` in `site/src/pages/format.ts`. While it is empty, every link to the form and every sentence that points to one hides.
- **Discussion goes to a Reddit thread**, the launch post on r/cormacmccarthy, linked from the About page once it exists, with a note that it may hold spoilers.
- No GitHub issue links for readers.

## Alternatives

- **Giscus.** Free, but posting needs a GitHub account, and threads on each place would show readers' talk of later events, which spoiler mode cannot filter.
- **Google Forms.** Free and prefillable, but its fields are opaque `entry.NNN` keys and it carries Google's branding.
- **Formspree or Web3Forms**, a form built into the site. No new tab, but the form, its errors and its spam handling would be ours to build. Formspree's free plan takes 50 submissions a month.
- **Hyvor Talk.** Guest comments, but about €50 a year, against the $0 budget.

## Consequences

- Suggestions are private to the owner. Nothing a reader writes shows on the site, so it cannot spoil the book.
- The site loads no third-party script for feedback. Tally sees only readers who open the form.
- A suggestion arrives by email, not as an issue, so the owner tracks it by hand.
- The Reddit post locks after six months unless the subreddit's moderators have turned that off, and the link then needs a new thread.
