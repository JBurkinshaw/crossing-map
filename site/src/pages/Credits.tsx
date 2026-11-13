import type { ReactNode } from 'react'
import { CAMPBELL_CREDIT, CAMPBELL_GUIDE } from '../data/translations'
import { REPO_URL } from './format'

// Every source the site uses, with the credit its terms ask for (plan section 3). `credit` is the wording
// shown wherever the source appears; `todo` marks wording not yet checked against the source's own terms.
type Credit = { name: string; link?: string; use: ReactNode; licence: string; credit?: string; todo?: string }

const COPERNICUS =
  'produced using Copernicus WorldDEM-30 © DLR e.V. 2010-2014 and © Airbus Defence and Space GmbH 2014-2018 provided under COPERNICUS by the European Union and ESA; all rights reserved'

const SECTIONS: { title: string; credits: Credit[] }[] = [
  {
    title: 'The book',
    credits: [
      {
        name: 'Cormac McCarthy, The Crossing',
        use: 'The novel this map follows. Page numbers are to the Vintage edition. No passage of the novel is reproduced here; the notes are our own words.',
        licence: 'In copyright',
      },
      {
        name: CAMPBELL_CREDIT,
        link: CAMPBELL_GUIDE,
        use: (
          <>
            <cite>A Translation of Spanish Passages in The Crossing</cite>, hosted by the Cormac McCarthy Society.
            The site does not copy the guide: it writes its own translations and links each one to the matching
            page of the guide.
          </>
        ),
        licence: 'In copyright; linked, not copied',
        credit: CAMPBELL_CREDIT,
      },
      {
        name: 'James Luther Bell, Contextualizing Cormac McCarthy’s Border Trilogy: An Annotative Approach',
        use: (
          <>
            PhD dissertation, Texas Tech University, 2000. Its index of the novel’s places, its local research around
            Cloverdale and its map of Hidalgo County were used to check and correct places on this map. Notes that
            draw on it cite the page, in our own words.
          </>
        ),
        licence: 'In copyright; facts used, text not copied',
        credit: 'Bell 2000',
      },
      {
        name: 'Joe Hazelton, Cormac McCarthy “The Crossing” (Gaia GPS)',
        link: 'https://www.gaiagps.com/public/QVoNQ0FcmpOf9KOEQVRqw6l4',
        use: (
          <>
            A reader’s map of the novel’s places, shared on{' '}
            <a href="https://www.reddit.com/r/cormacmccarthy/comments/18wu63g/map_of_the_crossing/">r/cormacmccarthy</a>.
            Its pins were compared with every place here; where they agree or led to a correction, the place says so.
          </>
        ),
        licence: 'Used with credit',
        credit: 'Joe Hazelton’s map',
      },
    ],
  },
  {
    title: 'Elevation and relief',
    credits: [
      {
        name: 'Copernicus DEM GLO-30',
        link: 'https://registry.opendata.aws/copernicus-dem/',
        use: 'The 30 m elevation model behind the hachures, contours, summits and passes, and the Raised view.',
        licence: 'Copernicus DEM licence: free use, with this notice. The organisations in charge of the Copernicus programme by law or by delegation do not incur any liability for any use of the Copernicus WorldDEM-30.',
        credit: COPERNICUS,
      },
      {
        name: 'AWS Terrain Tiles (Mapzen and Tilezen)',
        link: 'https://registry.opendata.aws/terrain-tiles/',
        use: 'The terrain shaded in the browser for the hillshade and the Tilted view. The tiles mix several sources; in this map’s region they are these two.',
        licence: 'Public domain (USGS); INEGI free-use terms',
        credit: '3DEP, SRTM and GMTED2010 terrain data courtesy of the U.S. Geological Survey. Source: INEGI, Continental relief, 2016.',
      },
      {
        name: 'Daniel Huffman, Hachures',
        link: 'https://github.com/pinakographos/Hachures',
        use: (
          <>
            The script that draws the hachures, run in QGIS. An adapted copy is kept, under its own licence, in{' '}
            <a href={`${REPO_URL}/tree/main/pipeline/relief/hachures`}>pipeline/relief/hachures/</a>, with a list of
            every change. The lines it generates are this site’s data.
          </>
        ),
        licence: 'GPL-3.0',
      },
    ],
  },
  {
    title: 'Rivers, borders and roads',
    credits: [
      {
        name: 'INEGI, Red Hidrográfica escala 1:50 000 edición 2.0',
        link: 'https://www.inegi.org.mx/temas/hidrografia/',
        use: 'The courses of named rivers in Sonora and Chihuahua on the classic map, and streams on the Mexico side in the Raised view.',
        licence: 'INEGI free-use terms, attribution required',
        credit: 'Fuente: INEGI, Red Hidrográfica escala 1:50 000 edición 2.0',
      },
      {
        name: 'USGS National Hydrography Dataset (NHD)',
        link: 'https://www.usgs.gov/national-hydrography',
        use: 'Streams on the US side, and the rivers some routes follow.',
        licence: 'Public domain',
        credit: 'USGS National Hydrography Dataset courtesy of the U.S. Geological Survey',
      },
      {
        name: 'US Census Bureau: TIGER/Line and cartographic boundary files',
        link: 'https://www.census.gov/geographies/mapping-files.html',
        use: 'County lines (cartographic boundaries, 2023, 1:500,000), and the roads some routes follow (TIGER/Line).',
        licence: 'Public domain',
        credit: 'County lines and roads courtesy of the U.S. Census Bureau (TIGER)',
      },
      {
        name: 'Natural Earth',
        link: 'https://www.naturalearthdata.com/',
        use: 'Borders, the Mexican states, lakes, roads and railroads of the base map, and the rivers outside the basins INEGI’s network covers.',
        licence: 'Public domain; no credit required',
        credit: 'Made with Natural Earth',
      },
    ],
  },
  {
    title: 'Place names',
    credits: [
      {
        name: 'USGS Geographic Names Information System (GNIS)',
        link: 'https://www.usgs.gov/tools/geographic-names-information-system-gnis',
        use: 'Names and locations of places, summits and passes in New Mexico and Arizona.',
        licence: 'Public domain',
        credit: 'Place names courtesy of the U.S. Geological Survey (GNIS)',
      },
      {
        name: 'GeoNames',
        link: 'https://www.geonames.org/',
        use: 'Names and locations of places, summits and passes in Sonora and Chihuahua.',
        licence: 'CC BY 4.0',
        credit: 'GeoNames',
      },
      {
        name: 'Wikidata',
        link: 'https://www.wikidata.org/',
        use: 'Locations for a few places the other gazetteers lack.',
        licence: 'CC0',
      },
    ],
  },
  {
    title: 'The satellite map',
    credits: [
      {
        name: 'MapTiler',
        link: 'https://www.maptiler.com/copyright/',
        use: 'Satellite imagery for the Satellite, Compare and Land colour views, and the Topo basemap, on MapTiler’s free plan. The MapTiler logo shows on the map whenever either does.',
        licence: 'MapTiler terms (non-commercial free plan)',
        credit: '© MapTiler © OpenStreetMap contributors',
      },
      {
        name: 'OpenStreetMap',
        link: 'https://www.openstreetmap.org/copyright',
        use: 'Data within MapTiler’s satellite map.',
        licence: 'ODbL',
        credit: '© OpenStreetMap contributors',
      },
    ],
  },
  {
    title: 'Type',
    credits: [
      {
        name: 'IM Fell types, digitally reproduced by Igino Marini',
        link: 'https://iginomarini.com/fell/',
        use: 'The typeface of the map’s labels: IM Fell English, roman, italic and small capitals.',
        licence: 'SIL Open Font License 1.1',
        credit: 'Copyright (c) 2010, Igino Marini (mail@iginomarini.com)',
      },
    ],
  },
  {
    title: 'Style references',
    credits: [
      {
        name: 'David Rumsey Map Collection',
        link: 'https://davidrumsey.com/maps5853.html',
        use: (
          <>
            The Wheeler Survey’s Atlas Sheet 83 (1876) and other period maps, studied for the hachure style; the{' '}
            <a href={`${REPO_URL}/blob/main/docs/inspiration/rumsey.md`}>list</a> gives each one. Nothing from them is
            reproduced.
          </>
        ),
        licence: 'Links only',
      },
      {
        name: 'Cartographers’ Guild',
        link: `${REPO_URL}/blob/main/docs/inspiration/guild.md`,
        use: 'Tutorials and threads read for the hand-drawn style; the index lists each one. Nothing from them is reproduced.',
        licence: 'Links only',
      },
    ],
  },
]

export function Credits() {
  return (
    <>
      <p className="lede">
        The map is drawn from public data, and every source is credited here with the wording its terms ask for. The
        map itself shows the terrain credits wherever the shaded relief or the Tilted view shows, and MapTiler’s
        logo and credit wherever the satellite imagery shows.
      </p>
      {SECTIONS.map((section) => (
        <section key={section.title}>
          <h2>{section.title}</h2>
          <dl className="credits">
            {section.credits.map((c) => (
              <div key={c.name}>
                <dt>{c.link ? <a href={c.link}>{c.name}</a> : c.name}</dt>
                <dd>
                  {c.use}
                  <div className="meta">Licence: {c.licence}</div>
                  {c.credit && <blockquote>{c.credit}</blockquote>}
                  {c.todo && <div className="todo">TODO: {c.todo}</div>}
                </dd>
              </div>
            ))}
          </dl>
        </section>
      ))}
      <h2>This site</h2>
      <p>
        The story data, notes and translations written for this site are CC BY 4.0. The code is MIT, except the
        hachure script, which keeps its GPL-3.0 licence. See the <a href="#/data">Data page</a> and the{' '}
        <a href={REPO_URL}>repository</a>.
      </p>
    </>
  )
}
