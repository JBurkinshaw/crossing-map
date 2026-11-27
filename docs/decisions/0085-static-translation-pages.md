# 0085. Static pages of the translations, for search engines

Status: accepted (2026-11-27). Amends 0083, and makes an exception to the spoiler rule of design section 11.
Phase: P1 (brought forward by the owner for the launch)

## Context

People search for translations of the Spanish in *The Crossing* more than for anything else the site holds. The site's 916 translations exist only in `translations.json`, which the app draws in its panel, so search engines never see them. Decision 0084 gave the site its tags and sitemap, but search engines still see one page.

A page that a search engine can read has to show its lines without the app, so it cannot know how far the reader has read. Design section 11 says nothing past the reader's progress shows anywhere. The owner accepted these pages as an exception, with the safeguards below, on 2026-11-27.

## Decision

- **Five plain HTML pages**, written by the build beside the app: an index at `/translations/` and one page per Part at `/translations/part-1/` to `/translations/part-4/`. `site/scripts/translation-pages.ts` writes them from `data/translations.json`, in the book's order. They need no JavaScript.
- **Each line shows** its Spanish incipit (at most five words, as in the app), its page in the Vintage paperback, this site's English, and, where Campbell's guide lists it, a link to the guide with the page it is listed under. The sorted word lists of decision 0047 are not shown, as in the app. Nothing else from the data is shown: no speaker, no place, and no episode summary.
- **Spoilers.** A notice above the first line says the page holds spoilers and points to the map, which hides them. Each episode is a closed `<details>` labelled only by its number, its pages and its count of lines. Every line sits in a `data-nosnippet` block, so Google indexes the text but never quotes a line in a search result. The index shows no lines, and its notice sits above the links to the Parts.
- **Search tags.** Each page has its own title and description, and on the release a canonical link and the preview image (decision 0084). The preview's copies have the `noindex` tag. The sitemap lists the five pages, and the app's `<noscript>` text links to the index.
- **A test** (`site/scripts/translation-pages.test.ts`) builds the pages from the published data and checks, for each Part, that every line shows once as its published incipit of at most five words, that the notice comes before the first episode, that no episode is open, that every line is inside a `data-nosnippet` block, and that no episode summary appears.
- **Counting.** On the release, each page counts its own visit with the same request as `site/src/analytics.ts`, under its path (`/translations/part-1`, for example). This amends decision 0083, whose page paths were the app's seven routes.
- **Links into the app.** Each page links to the map, which opens at the reader's own place. No line links to its place on the map: a link to a stop or place past the reader's progress would undo the map's spoiler mode.

## Alternatives

- **Path routes for the app**, rendered on the server or prerendered. They need a framework or a renderer, for pages that a short script can write.
- **One page for the whole book.** Fewer pages to rank, and one of over 200 KB, with all four Parts' spoilers behind one notice.
- **Pages per episode.** 41 small pages, each easy to rank for little, and the book's episodes are not how readers search.
- **A deep link from each line to its place.** Useful, but it needs the app to refuse a place past the reader's progress first.

## Consequences

- The pages are written when the site is built (`npm run build`), not by the dev server. Build the site and serve `dist/` to see them.
- A change to the published translations changes the pages at the next deploy.
- The spoiler-leak walk (decision 0054) checks the app, not these pages. The test above is their check.
