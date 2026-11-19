# Choosing the licences

This page explains which licences the project uses, why, and what to avoid. It is a reading of the licence texts linked under Sources, not legal advice. The per-source checklist is in `review/licences/README.md`.

## Recommendation

- **Code: keep MIT.** The vendored hachure generator in `pipeline/relief/hachures/` stays GPL-3.0 with its own `LICENSE`. It doesn't make the rest of the repository GPL, and the hachure lines it draws are not GPL.
- **Data and notes: CC BY 4.0, with two stated exceptions** (decision 0045). Layers made from the Copernicus DEM stay under the Copernicus DEM licence as well, and quotations from the novel, with the word lists and English translations made from them, are not licensed at all (decision 0047).
- **Don't switch to CC0, ODbL, CC BY-SA, or any NonCommercial (NC) licence.** Each one breaks a source's terms or a reader's freedom to reuse.

## Code

MIT asks one thing of a reuser: keep the copyright and licence notice ([choosealicense.com](https://choosealicense.com/licenses/)). Apache-2.0 adds a patent grant and a duty to mark changes, which matter for companies, not for a hobby map. Either would work, so there's no reason to change.

**The GPL folder.** The GPL FAQ treats separate programs shipped side by side as an "aggregate": each keeps its own licence ([MereAggregation](https://www.gnu.org/licenses/gpl-faq.html#MereAggregation)). The site and most of the pipeline never touch the generator. `pipeline/relief/run_hachures.py` runs it with `exec()` in one QGIS process, so the runner and the generator together form one GPL program. That's fine, because MIT is compatible with GPL. QGIS itself is GPL, so nothing new arises.

**The generator's output.** The FAQ says a program's output takes the copyright status of its input, not of the program ([GPLOutput](https://www.gnu.org/licenses/gpl-faq.html#GPLOutput), [WhatCaseIsOutputGPL](https://www.gnu.org/licenses/gpl-faq.html#WhatCaseIsOutputGPL)). The hachures come from the Copernicus DEM, so they follow its licence, not the GPL.

The repository already does what the GPL asks: the full licence text, Huffman's credit, and a list of changes in `pipeline/relief/hachures/README.md`.

## Data

**CC BY sources into CC BY data.** CC BY 4.0 lets you put your own licence on adapted material, provided it doesn't stop others from complying with the original. CC BY meets that test. You must credit each source, link its licence, and say you changed it ([CC BY 4.0, sections 3(a) and 4](https://creativecommons.org/licenses/by/4.0/legalcode.en)). That covers GeoNames, GMBA, the CEC land cover, and GRanD.

**Why not CC0.** CC0 waives all conditions, including the credit GeoNames, GMBA, the CEC, and GRanD require. You can't waive someone else's condition.

**INEGI.** INEGI's [Términos de Libre Uso](https://www.inegi.org.mx/inegi/terminos.html) allow copying, adapting, and commercial use. In return you must:

- credit "Fuente: INEGI" with the product's name and date
- tell users about any analysis or transformation
- not imply INEGI's endorsement.

None of this conflicts with CC BY. INEGI doesn't say so itself, so this is a reading, not INEGI's statement.

**Copernicus DEM.** This is the one real catch. The [licence](https://documentation.dataspace.copernicus.eu/APIs/SentinelHub/Data/DEM/resources/license/License-COPDEM-30.pdf) (Article 6) asks for three things:

- the notice "produced using Copernicus WorldDEM-30 © DLR e.V. 2010-2014 and © Airbus Defence and Space GmbH 2014-2018 provided under COPERNICUS by the European Union and ESA; all rights reserved"
- its liability disclaimer
- downstream users bound by the same obligations.

CC BY forbids adding conditions downstream. So the DEM-derived layers (glyphs, hachures, contours, the Oblique archives) shouldn't be presented as plain CC BY. Label them "derived from the Copernicus DEM, subject to its licence". Each feature's `source_licence` already does this, `data/README.md` carries the notice, and `data/LICENSE` says so too.

**Joe Hazelton's map.** He gave permission with credit. That isn't a CC BY licence, so his map's data can't be republished under CC BY. None is: no geometry comes from his pins. The reasoning texts only say where his map agrees or differs, which is a fact. Keep it that way, or ask him before copying a pin.

**OpenStreetMap.** OSM's licence, the ODbL, is share-alike. A database built from OSM data must stay under the ODbL ([OSMF Licence FAQ](https://osmfoundation.org/wiki/Licence/Licence_and_Legal_FAQ)). No OSM data is in the downloads. MapTiler's maps load OSM data in the reader's browser, which needs only the on-map credit (decision 0043).

## Text

- **Your notes.** Summaries and reasoning in your own words can be CC BY. Copyright covers expression, not facts, places, or plot.
- **English translations.** They are this site's wording, but translating the novel is McCarthy's right, so they stay out of the CC BY grant (decision 0047). They are published as a reading aid and commentary.
- **Spanish word lists.** A long line's other words, in alphabetical order, for search only. Sorted, they are not the line, but they come from it, so they stay out of the grant too.
- **Spanish incipits.** These are the opening words of short lines, a few words each. Words and short phrases aren't copyrightable ([US Copyright Office, Circular 33](https://www.copyright.gov/circs/circ33.pdf)), and brief quotation for commentary is the classic fair-use case. Keep them short, credit the novel, and leave them out of the CC BY grant.

## Foot-guns

1. **CC0 over CC BY inputs.** It drops credits you're obliged to pass on.
2. **Plain CC BY on Copernicus-derived layers,** or the notice left off.
3. **Any OSM, ODbL, or BY-SA data in the downloads.** Share-alike would pull the whole database under that licence.
4. **An NC source or an NC licence.** It clashes with the open inputs, and a portfolio link may count as commercial.
5. **Relicensing what isn't yours:** Hazelton's pins, Bell's text, or McCarthy's words.

## What `data/LICENSE` says

CC BY 4.0 was confirmed on 2026-11-16 (decision 0045). `data/LICENSE` grants it for the data and notes, except where a feature's `source_licence` says otherwise. It adds two exceptions: the Copernicus-derived layers are also under the Copernicus DEM licence, and the quotations from the novel, the word lists and the English translations are not licensed.

## Not verified

- The GPL-3.0 wording on marking changes was taken from memory, not re-read. The hachure README's change list meets it either way.
- GMBA, the CEC land cover, and Global Dam Watch were re-read on 2026-11-18, from GMBA's `LICENSE` file, the CEC's terms of use, and the Global Dam Watch technical documentation. All three are CC BY 4.0.
- INEGI makes no statement on CC BY compatibility.

## Sources

- [choosealicense.com](https://choosealicense.com/licenses/)
- [GNU GPL FAQ](https://www.gnu.org/licenses/gpl-faq.html)
- [CC BY 4.0 legal code](https://creativecommons.org/licenses/by/4.0/legalcode.en) and the [Creative Commons FAQ](https://creativecommons.org/faq/)
- [INEGI, Términos de Libre Uso](https://www.inegi.org.mx/inegi/terminos.html)
- [Copernicus DEM licence](https://documentation.dataspace.copernicus.eu/APIs/SentinelHub/Data/DEM/resources/license/License-COPDEM-30.pdf)
- [GeoNames, About](https://www.geonames.org/about.html)
- [OSMF Licence and Legal FAQ](https://osmfoundation.org/wiki/Licence/Licence_and_Legal_FAQ)
- [US Copyright Office, Circular 33](https://www.copyright.gov/circs/circ33.pdf)
