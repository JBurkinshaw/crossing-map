# 0083. Visits counted with GoatCounter, and a Privacy section

Status: accepted (2026-11-26). Adds to 0005 (the MapTiler SDK's telemetry is turned off).
Phase: P1 (brought forward from the Phase 2 backlog by the owner)

## Context

The owner wants to see what readers use: which pages, and which of the map's views. The roadmap asked for something simple and free, preferably without cookies, so that the site needs no consent banner. It named GoatCounter and Cloudflare Web Analytics, with Google Analytics acceptable but not preferred.

The site also said nothing about privacy. It has no server of its own, but three services see a reader's request: GitHub Pages, MapTiler (Satellite and Topo only) and Tally (the suggestion form only). The reader's place in the book is in the address (`#stop=`) and in `localStorage`, and a count of visits must not turn into a record of how far each reader has read.

## Decision

- **GoatCounter's hosted service counts visits**, under the site code `crossing-map`. The dashboard is private to the owner.
- **Only the release counts.** The site code reaches the build as `VITE_GOATCOUNTER`, which the deploy workflow sets for the build of `main` alone. The dev server, the preview at `/preview/` and the builds the tests run against send nothing. Automated browsers send nothing either.
- **The site sends the counts itself** (`site/src/analytics.ts`), with the request GoatCounter's `count.js` makes but fewer fields: the path, the referring page, the screen width and whether it is an event. It sends no page title and no query string, and it loads no script from GoatCounter.
- **A page's path is its route**, one of the router's seven (`/`, `/about`, `/open-questions` and so on), never the address bar's hash. The reader's stop and the map's camera are not sent.
- **Events come from a fixed list**, and a name never holds a place, a stop or an episode:
  - `basemap-satellite`, `basemap-topo`, `basemap-compare`
  - `view-tilted`, `view-oblique`
  - `read-on`
  - `search-used` (a search result was picked, not what was searched for)
  - `feedback-correction`, `feedback-translation`, `feedback-general` (a link to the form was followed)
  - `data-download`.
- **GoatCounter's "Individual pageviews" setting stays off**, its default, so it keeps totals by hour and day and no row for each visit. Its Languages setting stays off too.
- **The MapTiler SDK's telemetry is off** (`maptilersdk.config.telemetry = false`). By default the SDK reports its version, the API key and which features are on.
- **The About page has a Privacy section**: a plain opening, then where the reader's place is kept, the count of visits, what happens to a suggestion, and the services that see a request, with a link to each one's privacy policy. The lines about GoatCounter show only in a build that counts, and the lines about Tally only while the form is on.

## Alternatives

- **Cloudflare Web Analytics.** Free, and it works on a site Cloudflare does not serve. But it has no custom events ("Not yet", its FAQ), so it cannot say which views are used. Its documentation says nothing about hash routes, cookies or IP addresses, it thins data to about 10% after seven days, and it shows six months.
- **Google Analytics.** It sets cookies, so it needs a consent banner.
- **GoatCounter's own `count.js`.** It counts each page from `location.pathname`, binds click handlers and reads a `localStorage` key. Sending the same request from our own code means one host fewer for the reader's browser to reach, and the site decides every field.
- **Self-hosting GoatCounter.** It needs a server, which the site does not have.
- **No analytics.** Free of any third party, but the owner could not tell whether the Oblique view, search or the data downloads are used.

## Consequences

- GoatCounter's documentation was read on 2026-11-26. It says it stores no IP address and nothing in the browser, tells visits apart for eight hours in memory, and keeps its data at Hetzner in Finland and Germany. It is free "for reasonable public usage" and gives no fixed limit.
- Blockers that use the EasyPrivacy list stop the count, so the numbers are a floor.
- The count endpoint's fields are GoatCounter's, not ours. If they change, counts stop arriving and nothing on the site breaks.
- A new thing to count needs a new name in `CountedEvent`, which is where the rule about places and episodes is kept.
- A move to another domain keeps the counts, as paths are routes and the site code does not depend on the address.
- The owner holds what readers send through the form, so the Privacy section says how to have a suggestion deleted: through the form.
