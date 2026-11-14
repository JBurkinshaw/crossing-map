# Data sources

Where each input to the pipeline and tile builds comes from, and where it is cached. Every input is downloaded by hand once into `private/cache/` (git-ignored), so builds make no network requests unless noted. Licences and credit lines are in [`../data/README.md`](../data/README.md) and on the site's Credits page.

## Base map (`private/cache/basemap/`)

- **Natural Earth 10m**, public domain, from <https://naciscdn.org/naturalearth/10m/>: admin 0 boundary lines, admin 1 states and lines, rivers and lake centrelines (with the North America supplement), lakes (with the North America supplement), railroads (North America), roads, and populated places.
- **US Census cartographic boundary counties**, 2023, 1:500k, public domain: <https://www2.census.gov/geo/tiger/GENZ2023/shp/cb_2023_us_county_500k.zip>
- **IM Fell English, Italic, and SC** by Igino Marini, SIL Open Font License, from <https://github.com/google/fonts>, in `private/cache/basemap/fonts/`.

## Water (`private/cache/hydro/`)

- **USGS NHD Best Resolution**, public domain, HU8 shapefiles from <https://prd-tnm.s3.amazonaws.com/StagedProducts/Hydrography/NHD/HU8/Shape/>, in `nhd/`. The first six units cover the bootheel watersheds: 13030201, 13030202, 15040006, 15080301, 15080302, 15080303. A further 67 cover every US basin a named river crosses: 11080001, 11080003, 11080006, 11080007, 11090104, 12050005, 13020101, 13020102, 13020201, 13020203, 13020204, 13020205, 13020207, 13020211, 13030101, 13030102, 13040100, 13040201, 13040203, 13040205, 13060001, 13060003, 13060004, 13060007, 13060010, 13060011, 13070001, 13070007, 14070006, 14080105, 14080106, 14080204, 15010001, 15010002, 15010003, 15010005, 15020001, 15020002, 15020003, 15020006, 15020007, 15020008, 15020013, 15020016, 15030201, 15030203, 15030204, 15040001, 15040002, 15040005, 15050100, 15050202, 15050203, 15050301, 15050303, 15050304, 15060101, 15060103, 15060106, 15060202, 15070101, 15070102, 15070103, 15070104, 15070201, 15070203, 15080103.
- **INEGI Red Hidrográfica edición 2.0** (1:50,000, 2010, shapefile), INEGI free-use terms, from <https://www.inegi.org.mx/temas/hidrografia/#descargas>, in `inegi/`. Download URL pattern: `https://www.inegi.org.mx/contenidos/productos/prod_serv/contenidos/espanol/bvinegi/productos/geografia/hidrogeolo/region_hidrografica/<product>_s.zip`. Regions and product numbers:

  | Region | Product | Holds |
  | --- | --- | --- |
  | RH07 Río Colorado | 702825006982 | |
  | RH08 Sonora Norte | 702825006983 | |
  | RH09 Sonora Sur | 702825006984 | The Yaqui basin: Bavispe, Batepito, Papigochic |
  | RH10 Sinaloa | 702825006985 | |
  | RH24 Bravo-Conchos | 702825006999 | |
  | RH34 Cuencas Cerradas del Norte | 702825007009 | Casas Grandes, Santa María, Del Carmen |
  | RH35 Mapimí | 702825007010 | |

## Places (`private/cache/gazetteer/`)

- **USGS GNIS** Domestic Names for New Mexico and Arizona, public domain: <https://prd-tnm.s3.amazonaws.com/StagedProducts/GeographicNames/DomesticNames/DomesticNames_NM_Text.zip> and `..._AZ_Text.zip`.
- **GeoNames** Mexico dump, CC BY 4.0: <https://download.geonames.org/export/dump/MX.zip>
- **Wikidata**, CC0, through its API, at most one request a second, every answer cached.

## Roads (`private/cache/roads/tiger/`)

- **US Census TIGER 2023 roads**, public domain, by county: Cochise, Arizona (04003), and Grant (35017), Hidalgo (35023), Luna (35029), and Sierra (35051), New Mexico. From <https://www2.census.gov/geo/tiger/TIGER2023/ROADS/>.

## Roads in Mexico (`private/cache/roads/inegi/`)

- **INEGI Red Nacional de Caminos (RNC) 2024** (shapefile, 720 MB, product 794551132166), INEGI free-use terms, credit "Fuente: INEGI, Red Nacional de Caminos (RNC) 2024", from <https://www.inegi.org.mx/contenidos/productos/prod_serv/contenidos/espanol/bvinegi/productos/geografia/caminos/2024/794551132166_s.zip>, in `raw/`. Layer `red_vial`, clipped to 110.4 to 106.3° W, 27.9 to 32.1° N into `tracks.geojson` with `kind` (`TIPO_VIAL` and surface, lower case) and `name`. `crossing.least_cost` uses the unpaved tracks (`camino, tierra`, `camino, grava`) and footpaths (`vereda`) as road corridors.

## Elevation (`private/cache/dem/`, `private/cache/terrain/`)

- **Copernicus GLO-30 DEM**, 1° COG tiles from AWS open data, no login (decision 0011), in `dem/copernicus/` (the story box) and `dem/copernicus-region/` (the wider region). Fetched by `crossing.fetch_dem`.
- **AWS Terrain Tiles** (Terrarium PNG) at zoom 5–10 for the story box, in `terrain/`. Fetched by `tiles.build_terrain`.

## Translations and sources (`private/cache/translations/`, `private/sources/`)

- **Campbell's translation guide** PDF, downloaded once (see section 8 of [`design.md`](design.md) for the link). Never committed.
- **Bell (2000)** and Joe Hazelton's Gaia waypoints, in `private/sources/`. Never committed.

## Photos (`private/cache/photos/`)

- **Wikimedia Commons and Wikidata** API answers, one request at a time, cached by `crossing.photos`.
