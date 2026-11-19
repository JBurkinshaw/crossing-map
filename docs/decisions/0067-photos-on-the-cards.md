# 0067. Photos on the cards

Status: accepted (2026-11-18)
Phase: P1

## Context

`crossing.photos` found up to five Commons photos for each place and stop (`review/stage-6/photos-README.md`), and the owner picked 75 of them for 44 places in `review/stage-6/photos.csv`. On 2026-11-18 the owner also settled the two open questions of that search: aerial views stay dropped, and the places with no Wikidata link get no Wikidata search. Plan section 10 asks for small WebP files with a TASL credit (title, author, source, licence) under each photo and on the Credits page. Plan section 3 allows only public domain, CC0, CC BY and CC BY-SA files, and section 11 asks for visible attribution wherever a photo shows.

A photo can also give the story away. Its place has a `first_seen`, but its title can name another place: two of the Animas Valley's photos are of the Lordsburg Mesa, and the reader meets Lordsburg in Part II.

## Decision

- **One module, two steps.** `crossing.photo_assets download` fetches each picked file once, the 960 px thumbnail in the CSV, at most one request every 2 seconds with the pipeline's User-Agent. It caches each answer in `private/cache/photos/files/` and logs each request there. A 429 or 503 waits for its Retry-After, or a doubling wait, and a wait over 10 minutes stops the run. `crossing.photo_assets build` makes no request. The first run made 73 requests for 75 picks, as two files are picked for two places each, and every answer was a 200.
- **640 px WebP, under 6 MB.** Each file is resized to 640 px on its long side, converted to sRGB, and saved as WebP at quality 80 with no EXIF, XMP or ICC data. Plan section 10 said 800 px. At 640 px the 73 files take 5.6 MB, and the card shows them at most 380 px wide, so 640 px is still sharp on a screen of twice the density. The build fails if the files pass 6 MB.
- **The files live in `site/public/photos/`, tracked in git.** They are part of the site, not of the open data: `data/` is copied whole into the site, so photos there would sit inside the CC BY folder and its downloads under other licences. `site/public/` already holds other tracked assets (the fonts, the sprite and the pass labels). `data/photos.json` holds the credits and points at each file by its path from the site's root.
- **`data/photos.json`** lists each place (or stop with no place of its own) with the stops that show its photos, and its picks in the owner's order. Each photo has its file and size, its Commons title, its author as plain text, its licence and licence URL, the date taken, its Commons page, how the search found it, and alt text. A JSON Schema checks it, and `crossing.validate` checks the places and stops, each file's size on disk, and the licences.
- **Credits come from Commons, cleaned.** HTML and hidden text are stripped from Commons' `extmetadata`. Where Commons gives a sentence or no author, `pipeline/seeds/photo-text.csv` sets one, with its reason. Peter Potrowl asks on Commons to be credited "© Peter Potrowl", so his four photos are. The two 1937 photos of Fort Bowie credit Frederick D. Nichols and the Historic American Buildings Survey, which their titles name. Bisbee credits Willjay at English Wikipedia, its uploader. The Emory Pass photo credits Samat Jain: its Flickr account writes that name upside down, and the same account is credited as Samat Jain on the Gila National Forest photo. The date is the date taken. The upload date never stands in for it.
- **Alt text is written by hand** in the same seed, from the title and the kind of view only: "Landscape photograph near Howells Ridge", "Photograph from 1937 of the ruins of Fort Bowie, looking west". It never says what the photo shows beyond its title. Where a title says little ("Mall"), the alt text gives the title in quotes.
- **A photo follows its place's spoiler rule.** It shows with its place, or with its stop for a stop with no place. Where its title, alt text or author names a place the reader meets later than the photo's own place, the build gives the photo that later `first_seen`, like a lead (decision 0065). Four photos have one: the two of the Lordsburg Mesa on the Animas Valley and the Lordsburg Playa on Road Forks show from 2-05, and the ruins of Paquimé on Casas Grandes from 2-08. The data half of the spoiler-leak test (decision 0054) checks that no photo shows early and that no photo's words name a place not yet met. The browser half checks every photo the panel shows.
- **On the card,** the photo comes after the opening text: on a place card after its kind and note, on a stop after its episode, synopsis and note, before the folds. So on a phone the drawer still opens on the story (decision 0060). The frame is 200 px tall, 160 px on phones, with the whole photo inside it on the paper, so a step to a photo of another shape moves nothing below it. The image is lazy-loaded with its width and height. A place with no photo shows nothing, not an empty frame.
- **A stepper for more than one photo:** Back and Next buttons with "1 of 3" between them, in the stop stepper's style but in faint ink, so they read as the photo's and not the journey's. They are real buttons, named "Back to the previous photo" and "Next photo" for screen readers, and the count is announced. They go round at the ends, so the pressed button keeps the focus. Nothing plays by itself.
- **The TASL line** under each photo: the title in quotes, the author, "Wikimedia Commons" linked to the file's page, and the licence linked to its deed (public domain files have none). The Credits page lists every photo the reader has reached, by place, with the same line and the date taken, and says that the photos keep their own licences.

## Alternatives

- **800 px, as plan section 10 said.** The same 73 files take 8.8 MB at 800 px, over the budget, for no gain at the card’s width.
- **The files in `data/photos/`.** `copy-data.mjs` would serve them with no change, but they would ship inside the CC BY data folder under their own licences, and every reuse of `data/` would carry them.
- **Hot-linking Commons thumbnails.** No files in the repository, but every card would ask Wikimedia's servers and tell them what the reader looks at, and a renamed or deleted file would break the card.
- **Cropping each photo to one shape.** The frame would be filled, but a crop is a change the CC BY credit must state, and the panoramas would lose most of their width.
- **The photo first, under the title.** It would make the card more pictorial, but on a phone the photo would fill the drawer's opening view and push the story down, against decision 0060.
- **Showing each photo at its place's episode whatever its title says.** Simpler, but the Credits page and the alt text would name Lordsburg and Paquimé before the reader meets them.

## Consequences

- The owner's later picks need only the CSV, `photo-text.csv` for the alt text, and the two commands. A new file is one more request.
- The site grows by 5.6 MB, all lazy-loaded: a reader downloads only the photos of the cards they open.
- The "today" captions of plan section 10 are not written. The TASL line and the date taken stand in for them for now.
- The CC BY-SA photos stay under BY-SA. They are shown unchanged, so the site's own licence is not affected.
- Aerial views stay dropped from the search, and places with no Wikidata link are searched by geosearch only. "Socorro aerial" is an aerial photograph the owner picked by hand, not one of the satellite or orthophoto files the search drops, so it stays.
