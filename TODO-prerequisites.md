# Prerequisites to clear

Work does not wait for these. Each line names what is missing, what is stubbed until it arrives, and how to clear it.

- [ ] **Licences.** MIT for code and CC BY 4.0 for data are in place as proposed in the plan, section 12. Confirm or change before launch.
- [ ] **MapTiler key.** Create a free account, restrict the key to `https://jburkinshaw.github.io` and `http://localhost:5173`, then set it as the repository variable `VITE_MAPTILER_KEY` and in `site/.env.local`. Until then the satellite basemap shows "unavailable".
- [ ] **Part I prototype data.** Export the places, stops, and notes from the claude.ai artifact into `private/prototype/`. Until then Part I is rebuilt from the plan, section 2.2.
- [ ] **micromamba / QGIS.** `micromamba` fails with a missing `libnettle.8.dylib`. Try `brew reinstall micromamba`. Needed for the hachure treatments in stage 3.
- [ ] **DRM-free EPUB.** Put it in `private/book/`. Needed for page anchors in stage 4.
- [ ] **Inkscape and `potrace` or `vtracer`.** Needed for vignettes in stage 6.
