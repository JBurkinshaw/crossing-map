# Prerequisites to clear

Work does not wait for these. Each line names what is missing, what is stubbed until it arrives, and how to clear it.

- [ ] **Licences.** MIT for code and CC BY 4.0 for data are in place as proposed in the plan, section 12. Confirm or change before launch.
- [x] **MapTiler key.** Created 11 November 2026; stored as the repository variable `VITE_MAPTILER_KEY` and in `site/.env.local`. Works from localhost.
- [x] **MapTiler allowed origin for Pages.** Fixed 11 November 2026; satellite works on the live preview.
- [ ] **Part I prototype data.** Export the places, stops, and notes from the claude.ai artifact into `private/prototype/`. Until then Part I is rebuilt from the plan, section 2.2.
- [ ] **micromamba / QGIS.** `micromamba` fails with a missing `libnettle.8.dylib`. Try `brew reinstall micromamba`. Needed for the hachure treatments in stage 3.
- [x] **DRM-free EPUB.** In `private/book/the-crossing.epub` (11 November 2026).
- [ ] **Inkscape and `potrace` or `vtracer`.** Needed for vignettes in stage 6.
- [ ] **Cartographers' Guild login.** Logged in on 11 November 2026; close the Chrome Canary window that `npm run guild-login` opened so the browsing run can use the profile. The forum is closed to logged-out visitors. In `tools/`, run `npm run guild-login`, log in (tick "Remember Me"), and close the window. Then `npm run guild-browse` saves screenshots to `private/inspiration/guild/` and titles to `docs/inspiration/guild.md`. Until then stage 2 styles from the Rumsey maps and the plan's own references.
- [ ] **INEGI river network for Sonora and Chihuahua.** No direct download link exists; INEGI publishes its 1:50,000 hydrography through its downloads portal (https://www.inegi.org.mx/temas/topografia/#Descargas). Download the river network (red hidrográfica) for the Bavispe, San Bernardino and Casas Grandes basins into `private/cache/hydro/inegi/`. Until then Mexican creeks outside the border watersheds are missing and the Cajon Bonita leg stays schematic.
