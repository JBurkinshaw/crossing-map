# Prerequisites to clear

Work does not wait for these. Each line names what is missing, what is stubbed until it arrives, and how to clear it.

- [ ] **Licences.** MIT for code and CC BY 4.0 for data are in place as proposed in the plan, section 12. Confirm or change before launch.
- [x] **MapTiler key.** Created 11 November 2026; stored as the repository variable `VITE_MAPTILER_KEY` and in `site/.env.local`. Works from localhost.
- [x] **MapTiler allowed origin for Pages.** Fixed 11 November 2026; satellite works on the live preview.
- [ ] **Part I prototype data.** Export the places, stops, and notes from the claude.ai artifact into `private/prototype/`. Until then Part I is rebuilt from the plan, section 2.2.
- [x] **micromamba / QGIS.** Reinstalled 11 November 2026: QGIS 4.2.3 in a micromamba environment. The hachure runs find it through `QGIS_ENV` (decision 0015).
- [x] **DRM-free EPUB.** In `private/book/the-crossing.epub` (11 November 2026).
- [ ] **Inkscape and `potrace` or `vtracer`.** Needed for vignettes in stage 6.
- [x] **Cartographers' Guild browsing.** Done 11 November 2026: 24 threads indexed in `docs/inspiration/guild.md`, with screenshots in `private/inspiration/guild/`. To browse again, run `npm run guild-login` in `tools/`, log in, close the window, then run `npm run guild-browse`.
- [ ] **INEGI river network for Sonora and Chihuahua.** No direct download link exists; INEGI publishes its 1:50,000 hydrography through its downloads portal (https://www.inegi.org.mx/temas/topografia/#Descargas). Download the river network ("Red hidrográfica", 1:50,000, version 2.0, shapefile) for the Yaqui basin, which holds the Bavispe and the San Bernardino (probably hydrological region RH09, Sonora Sur), and the Casas Grandes basin (probably RH34, Cuencas Cerradas del Norte). If the portal lists sub-basins instead, take the ones named for those rivers. Put the zip files, unopened, in `private/cache/hydro/inegi/`. Until then Mexican creeks outside the border watersheds are missing and the Cajón Bonito leg stays schematic.
