# 0084. Search engines and link previews

Status: accepted (2026-11-27). Amends 0083.
Phase: P1

## Context

The site should come up when someone searches for a map of *The Crossing*, or for translations of its Spanish. Today a search engine sees one HTML page with a title, a description and a line saying the map needs JavaScript. The pages are hash routes, which search engines treat as one address. A link shared on Reddit or in a chat shows as text, with no picture. The site has no canonical address, no structured data, no `robots.txt` and no sitemap.

Static pages for the translations would do the most for search, but they change the design and bend the spoiler rule, so they wait for the owner (`docs/roadmap.md`). This record covers the changes that need neither.

## Decision

- **One address drives every tag.** The deploy workflow passes the site's address (`SITE_URL`, decision 0003) to both builds. `site/scripts/seo.ts` writes the tags from it and the build's base path. A build without it, such as the dev server, gets none of them.
- **The title names the searches.** "The Crossing by Cormac McCarthy: a reading map and Spanish translations", in `<title>` and `og:title`. The pages keep their own short titles and restore the map's when the reader returns to it.
- **The release gets** a canonical link, `og:url`, `og:image` with its size and alt text, a `summary_large_image` Twitter card, and JSON-LD.
- **The preview gets** `og:url`, `og:image` and the card, so a shared link to it still shows the picture, and keeps its `noindex` tag. It has no canonical link and no JSON-LD.
- **The preview image** (`site/public/og-image.jpg`, 1200 × 630) is chosen by the owner: the Animas Valley and the Peloncillos in the Tilted view at zoom 11, north up, with the land cover, the she-wolf's route (J1), seven drawings of the trapping episodes, and the cartouche naming the map. The reading position is Part I, episode 6, so nothing later shows. A preview should show what the site does that a map of the region would not, and this view shows the terrain, the land cover and the drawings together. `tools/og-image.mjs` makes it again.
- **JSON-LD** describes the site as a `WebSite` about the novel, and the CC BY layers (decision 0045) as a `Dataset`, so Google Dataset Search can list them. Each layer is offered as GeoJSON and GeoParquet. The creator is the site itself, not a person, until the owner settles how the site credits its maker ("Portfolio framing" in `docs/roadmap.md`). `translations.json` is not in the dataset, because its English is not licensed (decision 0047).
- **`robots.txt` and `sitemap.xml`** are written for the release alone, at the root of the host. `robots.txt` allows everything, the preview included, so that crawlers reach the preview's `noindex` tag. The sitemap lists the root, the only address the site has until it has real paths.
- **The `<noscript>` text** says what the site holds, for crawlers that do not run JavaScript.
- **Shared links carry a tag.** A link the owner posts carries `?ref=` and a short name for where it was posted, such as `?ref=reddit-cm`. The site sends that name to GoatCounter as the referrer, as GoatCounter's own `count.js` does, so the counts say which post brought readers. Only a tag of up to 40 letters, digits, dots, hyphens and underscores is sent, and nothing else from the query string. This amends decision 0083, which sent no part of the query string.

## Alternatives

- **A ready-made plugin for head tags.** The tags are a dozen lines, and a plugin would add a dependency for them.
- **A static `robots.txt` in `site/public/`.** It would ship with the preview and the local builds too, naming a sitemap they do not have.
- **The opening view, framed.** It has the large title, but at link-preview size the map reads as a general map of the borderlands, and the drawings are too small to make out.
- **J1 in the Oblique view.** It shows the relief standing up, but seen from straight above it has no horizon, so it reads less as a landscape than the Tilted view.
- **The same view with the whole book shown.** It has more drawings and routes, but they show later journeys and drawings from later episodes, which give away where the story goes.
- **The key open.** It explains the lines, but at this size it covers a third of the picture.

## Consequences

- Nothing changes for search until the release is merged to `main`. The preview is not indexed.
- Search Console and Bing Webmaster Tools are the owner's to set up, with the sitemap at `https://thecrossingmap.com/sitemap.xml`.
- A new layer in `site/scripts/site-facts.ts` joins the dataset's downloads without a change here.
- The image does not follow the map. When the opening view changes, run `tools/og-image.mjs` again.
