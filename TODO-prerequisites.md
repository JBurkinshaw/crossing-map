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
- [x] **INEGI river network for Sonora and Chihuahua.** Done 12 November 2026: "Red hidrográfica edición 2.0" (1:50,000, 2010 edition, shapefile) for two whole hydrological regions, from https://www.inegi.org.mx/temas/hidrografia/#descargas. RH09 Sonora Sur (INEGI product 702825006984, 347 MB) holds the Yaqui basin with the Bavispe, Batepito and Papigochic. RH34 Cuencas Cerradas del Norte (702825007009, 151 MB) holds the Casas Grandes, Santa María and Del Carmen. Both zips pass an integrity test and are in `private/cache/hydro/inegi/`, unopened. RH08 (Sonora Norte) and RH24 (Bravo-Conchos) would fill the rest of the story box if it is wanted.
