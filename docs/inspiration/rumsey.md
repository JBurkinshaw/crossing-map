# David Rumsey Map Collection references

Period maps studied for the literary map's style (plan section 5.4, phase 1). The [David Rumsey Map Collection](https://www.davidrumsey.com/) licenses its images CC BY-NC-SA. That fits a free, non-commercial site with attribution, and it means anything derived from them (a traced overlay, a cropped detail) must be shared under the same licence. So no image, crop or tracing from these maps goes in this MIT repository. Preview images, when downloaded, stay in `private/inspiration/rumsey/`, which is git-ignored.

## How this list was made, and what is not yet checked

Written 13 November 2026. The collection's `robots.txt` disallows its catalogue search (`/luna/servlet/search`, `/luna/servlet/view/search`, `/luna/servlet/as`) and asks for a 500-second crawl delay. The first catalogue detail page requested, with that delay, returned a reCAPTCHA "Verify Access" page instead of the record. That is a bot check, so fetching stopped there and was not retried. No preview images were downloaded.

The records below come from search-engine results that quote the Rumsey catalogue. Titles, dates and scales agree across at least two records unless marked. Before you rely on a row, open its link in a browser and check:

1. The date, scale and list number.
2. Whether the record has a "View in Georeferencer" link (the **Geo** column).
3. Download the ordinary preview size (not full resolution) into `private/inspiration/rumsey/`.

**Geo** column: *yes* means a Rumsey Georeferencer record was seen in search results; *?* means not checked.

## Shortlist (plan section 5.4)

| Map | Date | Scale | Author or publisher | Record | List no. | Geo |
| --- | --- | --- | --- | --- | --- | --- |
| Wheeler Survey, Atlas Sheet 83, *Parts of Eastern and South Eastern Arizona, Western and South Western New Mexico* (geological atlas issue) | 1876 (some copies 1877) | 1:506,880 | G. M. Wheeler; engraved by Weyss, Herman & Lang | [detail](https://www.davidrumsey.com/luna/servlet/detail/RUMSEY~8~1~382~30089), [page](https://www.davidrumsey.com/maps5853.html) | 2738.088 | ? |
| Wheeler Survey, Atlas Sheet 84 (B), *Land Classification Map of Part of Southern New Mexico* | 1879 | 1:253,440 (to check) | G. M. Wheeler | [detail](https://www.davidrumsey.com/luna/servlet/detail/RUMSEY~8~1~397~40006) | ? | ? |
| Wheeler Survey, Atlas Sheet 84 (C), *Land Classification Map of Part of South Western New Mexico* (title to check) | 1878–79 | 1:253,440 | G. M. Wheeler | [detail](https://www.davidrumsey.com/luna/servlet/detail/RUMSEY~8~1~398~40007) | ? | ? |
| J. C. Mallery and J. W. Ward, *New Map of the Territory of Arizona, Southern California and Parts of Nevada, Utah and Sonora* | 1877 | 1:1,013,760 | Payot, Upham & Co.; lith. Britton, Rey & Co., San Francisco | [detail](https://www.davidrumsey.com/luna/servlet/detail/RUMSEY~8~1~1960~130141), [cover page](https://www.davidrumsey.com/maps76.html) | ? | ? |
| E. A. Eckhoff and P. Riecker, *Official Map of the Territory of Arizona* | 1880 | 1:823,680 | Graphic Co., New York | [page](https://www.davidrumsey.com/maps5457.html) | 2980 (from a dealer listing) | ? |
| *Rand McNally & Co.'s New Mexico* (pocket map, 25 cent series) | 1880 | 1:2,027,520 | Rand McNally, Chicago | [detail](https://www.davidrumsey.com/luna/servlet/detail/RUMSEY~8~1~214603~5501735) | ? | ? |
| S. A. Mitchell, *County Map of Arizona and New Mexico* | 1880 (entered 1879) | ? | S. A. Mitchell, Philadelphia | [detail](https://www.davidrumsey.com/luna/servlet/detail/RUMSEY~8~1~254655~5519464) | 0586.047 | ? |
| O. W. Gray, *New Mexico and Arizona* | 1874 (entered 1873) | ? | Stedman, Brown & Lyon | [detail](https://www.davidrumsey.com/luna/servlet/detail/RUMSEY~8~1~207022~3003101) | ? | ? |
| General Land Office, *Territory of New Mexico* | 1879 (1882 reissue unchanged) | 1:1,013,760 | GLO under J. A. Williamson; Julius Bien, New York | not identified; the plan's 1891 edition was not found | ? | ? |

What to learn from each, tied to the design brief (plan 5.1 and 5.2):

- **Wheeler Sheet 83.** The target style for Part I. Systematic hachures over a light grey under-tint, light from the north-west, flats left blank. Check how the Peloncillos, Animas and the bootheel ranges are hachured at this scale; it is the closest model for our DEM-driven hachures. Note the italic, spaced range names that follow the range axis, and how few towns there are.
- **Wheeler 84 (B) and (C).** Same base, with land classes in flat tints (grazing, timber, arable). Study how a tint sits under hachures without muddying them; this is the model for the P2 land-cover stipple on the Animas and Playas plains.
- **Mallery and Ward 1877.** One of the few US maps of the period that carries detail into Sonora. Study the lettering hierarchy (territory, county, range, town) and how the drawing thins out south of the line: what a surveyor leaves blank. County colour is a model for the "Mexico side a shade darker" token, if done as a flat wash.
- **Eckhoff and Riecker 1880.** The first official territorial map, with good Cochise County detail. Its places are those of 1880 (Douglas, founded in 1901, is missing), so use it for style, not names. Study road and trail styling and the spacing of small settlement names.
- **Rand McNally New Mexico 1880.** Hachures at a small scale. A model for the zoomed-out view, where each range is a few strokes; compare with the caterpillar style the plan wants only at the smallest zooms.
- **Mitchell and Gray.** Commercial atlas maps: study the borders (dash-dot international line, ribboned county edges), the hand-coloured county tints and the title lettering. Take the line work, not the busy decoration.
- **GLO New Mexico.** Land grants and survey lines; useful for the plain, public-record look of the US side, which contrasts with the Mexican side.

## Parts II–IV: northern Chihuahua and Sonora

| Map | Date | Scale | Author or publisher | Record | List no. | Geo |
| --- | --- | --- | --- | --- | --- | --- |
| International Boundary Commission, *Linea Divisoria entre Mexico y los Estados Unidos al Oeste del Rio Grande* (sheet series) | 1899–1901, survey 1891–94 | 1:60,000 | International Boundary Commission; engraved by R. F. Bartle & Co., Washington | [No. 1](https://www.davidrumsey.com/luna/servlet/detail/RUMSEY~8~1~36725~1200423) | 2171.001 to 2171.0xx | yes for No. 16; others ? |
| *Sheet No. 3, Department of Arizona* | 1876 (revised 1875 base) | 1:665,300 | J. C. Mallery and J. W. Ward, Office of the Chief of Engineers | [detail](https://www.davidrumsey.com/luna/servlet/detail/RUMSEY~8~1~222539~5505585) | ? | ? |
| Office of the Chief of Engineers, *Southwestern New Mexico* | 1883 | 1:475,200 | drawn by W. Kilp, Department of the Missouri | not identified on davidrumsey.com | ? | yes |
| Antonio García Cubas, *Atlas geográfico, estadístico e histórico de la República Mexicana*: the Sonora and Chihuahua plates | 1858 | ? | Imprenta de J. M. Fernández de Lara, Mexico | [atlas, Carta I](https://www.davidrumsey.com/luna/servlet/detail/RUMSEY~8~1~20083~570051); plate records not identified | ? | ? |
| Antonio García Cubas, *Atlas geográfico y estadístico de los Estados Unidos Mexicanos*: Sonora (Carta I) and Chihuahua (Carta II) | 1886 | ? | Debray Sucesores, Mexico | not identified | 5758 (from a dealer listing) | ? |
| *Rand McNally & Co.'s New Shippers' Railroad Map*, Southwest and Mexico section | 1891 | ? | Rand McNally, Chicago | [detail](https://www.davidrumsey.com/luna/servlet/detail/RUMSEY~8~1~200421~3000347) | ? | ? |

What to learn from each:

- **Boundary Commission sheets.** The border itself, surveyed in the years just before the book's events. Study the boundary line and numbered monuments, contour-and-hachure relief at large scale, and bilingual titling. The sheets that should cover the Part I and II crossing country (the 31°20' line from the bootheel corner west past San Bernardino and Agua Prieta) are probably Nos. 4–7, from the extent of No. 3 (108°24' to 107°40' W). Check the numbers in a browser.
- **Department of Arizona Sheet 3.** A military map of southern Arizona that reaches into Sonora; study trail and spring symbols and how water is marked in dry country.
- **Southwestern New Mexico, 1883.** Hachures and spot heights, uncoloured: a model of how much an ink-only map can carry, and a Rumsey georeferenced sheet over the bootheel.
- **García Cubas plates.** The Mexican side drawn by a Mexican mapmaker, as the plan asks. Study Spanish lettering conventions (Sierra, Río, Hacienda, Presidio), the drawing of the Sierra Madre, and the pre- and post-Gadsden boundary on the 1858 Chihuahua plate.
- **Rand McNally 1891 railroad map.** Shows the lines from El Paso and Nogales into Mexico. A reference for drawing railroads as fine ticked lines that stay below the route colours.

**Not found:** a Rumsey map of the Mexico North Western Railway (the Rio Grande, Sierra Madre and Pacific before 1909) or its surveys through Casas Grandes and Madera, and any Comisión Geográfico-Exploradora sheet for Chihuahua or Sonora. A browser search of the catalogue for "Nor-Oeste", "Sierra Madre" and "Casas Grandes" is the next step.

## Phase 2: georeferenced overlays

P2 shows period maps as raster overlays through the same swipe as satellite. From what was seen:

- Rumsey Georeferencer records were seen for *Southwestern New Mexico* (1883) and Boundary sheet No. 16. Stanford publishes a georeferenced copy of Boundary sheet No. 3 (CC BY-NC-SA).
- Wheeler Sheet 83 has an Old Maps Online footprint (rumsey/2738.088), which suggests but does not prove a georeferenced version. Check its record for a Georeferencer link.
- For any map without one, georeference in QGIS (plan 5.4).

Any overlay, being derived from a CC BY-NC-SA scan, is shared under CC BY-NC-SA and credited to the David Rumsey Map Collection, David Rumsey Map Center, Stanford Libraries.
