import { useEffect, useState, type ReactNode } from 'react'
import { CAMPBELL_CREDIT, CAMPBELL_GUIDE } from '../data/translations'
import type { PlacePhotos } from '../data/photos'
import type { Story } from '../data/story'
import { PhotoCredit } from '../panel/Photos'
import { shownAt } from '../spoiler/filter'
import { byId } from '../story/select'
import { REPO_URL, repoUrl } from './format'
import { LARGE_ART } from '../map/largeArt'

// Every source the site uses, with the credit its terms ask for (design section 3). `credit` is the wording
// shown wherever the source appears.
type Credit = { name: string; link?: string; use: ReactNode; licence: string; credit?: string }

const COPERNICUS =
  'produced using Copernicus WorldDEM-30 © DLR e.V. 2010-2014 and © Airbus Defence and Space GmbH 2014-2018 provided under COPERNICUS by the European Union and ESA; all rights reserved'

const SECTIONS: { title: string; credits: Credit[] }[] = [
  {
    title: 'The book',
    credits: [
      {
        name: 'Cormac McCarthy, The Crossing',
        use: 'The novel this map follows. Page numbers are to the Vintage edition. No passage of the novel is reproduced here; the notes are this site’s own words.',
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
        link: 'https://ttu-ir.tdl.org/bitstreams/ec52ab01-a89b-423d-aee5-92df180a15c4/download',
        use: (
          <>
            PhD dissertation, Texas Tech University, 2000. Its index of the novel’s places, its local research in the
            bootheel and its county map were used to check and correct places on this map. Notes that
            draw on it cite the page, in this site’s own words.
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
            Its pins were compared with every place here, and led to some corrections.
          </>
        ),
        licence: 'Credited, with the author’s permission',
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
        use: 'The 30 m elevation model behind the hachures, contours, summits and passes, and the Oblique view.',
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
            <a href={repoUrl('pipeline/relief/hachures')}>pipeline/relief/hachures/</a>, with a list of
            every change. The lines it generates are this site’s data.
          </>
        ),
        licence: 'GPL-3.0',
      },
      {
        name: 'Bernhard Jenny and Tom Patterson, Introducing Plan Oblique Relief',
        link: 'https://doi.org/10.14714/CP57.279',
        use: (
          <>
            <cite>Cartographic Perspectives</cite> 57 (2007). The method behind the Oblique view: every point moves
            north in proportion to its height, and ground behind higher ground is hidden. The site’s own code
            applies it to the map’s lines and land cover.
          </>
        ),
        licence: 'Method; cited',
      },
    ],
  },
  {
    title: 'Land cover',
    credits: [
      {
        name: 'Commission for Environmental Cooperation, North American Land Cover 2020 (30 m)',
        link: 'https://www.cec.org/north-american-environmental-atlas/land-cover-30m-2020/',
        use: (
          <>
            The land cover under the map, when the ground is set to Land cover: one Landsat classification for Mexico
            and the US, so the colours do not change at the border. Its classes are re-read with height (below), so
            the map’s classes are this site’s, not the CEC’s.
          </>
        ),
        licence: 'CC BY 4.0, transformed by this site',
        credit:
          'Commission for Environmental Cooperation (CEC). 2024. “North American Environmental Atlas - Land Cover 2020 30m”. North American Land Change Monitoring System. Canada Centre for Remote Sensing (CCRS), U.S. Geological Survey (USGS), Comisión Nacional para el Conocimiento y Uso de la Biodiversidad (CONABIO), Comisión Nacional Forestal (CONAFOR), Instituto Nacional de Estadística y Geografía (INEGI). Ed. 2.0, Raster digital data [30-m].',
      },
      {
        name: 'David E. Brown, ed., Biotic Communities: Southwestern United States and Northwestern Mexico',
        use: (
          <>
            University of Utah Press, 1994. The height bands that sort the CEC’s trees into gallery forest, oak
            woodland and pine (<a href={repoUrl('docs/decisions/0040-oblique-strokes-and-land-cover.md')}>decision 0040</a>).
          </>
        ),
        licence: 'Facts used; cited',
      },
    ],
  },
  {
    title: 'Rivers, borders and roads',
    credits: [
      {
        name: 'INEGI, Red Hidrográfica escala 1:50 000 edición 2.0',
        link: 'https://www.inegi.org.mx/temas/hidrografia/',
        use: 'The named rivers, the smaller streams and the lakes on the Mexico side of the vintage map, and streams on the Mexico side in the Oblique view.',
        licence: 'INEGI free-use terms, attribution required, transformed by this site',
        credit: 'Fuente: INEGI, Red Hidrográfica escala 1:50 000 edición 2.0, agosto de 2010',
      },
      {
        name: 'INEGI, Red Nacional de Caminos (RNC) 2024',
        link: 'https://www.inegi.org.mx/app/biblioteca/ficha.html?upc=794551132166',
        use: 'Its unpaved tracks and footpaths draw the modelled routes towards a road where the book has the rider on one (decision 0021). They are today’s tracks, standing in for the roads of the 1940s; the map does not draw them.',
        licence: 'INEGI free-use terms, attribution required, transformed by this site',
        credit: 'Fuente: INEGI, Red Nacional de Caminos (RNC) 2024',
      },
      {
        name: 'Global Dam Watch database v1.0, with GRanD v1.3',
        link: 'https://doi.org/10.6084/m9.figshare.25988293',
        use: 'The year each dam was finished, which decides the reservoirs the vintage map leaves out as built after the book (decision 0031). The map draws none of its shapes.',
        licence: 'CC BY 4.0, transformed by this site',
        credit: 'Lehner, B. et al. (2024), The Global Dam Watch database of river barrier and reservoir information for large-scale applications, Scientific Data; Global Dam Watch database v1.0, https://www.globaldamwatch.org',
      },
      {
        name: 'USGS National Hydrography Dataset (NHD)',
        link: 'https://www.usgs.gov/national-hydrography',
        use: 'The courses of the named rivers on the US side of the vintage map, streams on the US side, and the rivers some routes follow.',
        licence: 'Public domain',
        credit: 'USGS National Hydrography Dataset courtesy of the U.S. Geological Survey',
      },
      {
        name: 'US Census Bureau: TIGER/Line and cartographic boundary files',
        link: 'https://www.census.gov/geographies/mapping-files.html',
        use: 'County lines (cartographic boundaries, 2023, 1:500,000), and the roads some routes follow (TIGER/Line).',
        licence: 'Public domain',
        credit: 'County lines and roads courtesy of the U.S. Census Bureau (cartographic boundary files and TIGER/Line)',
      },
      {
        name: 'Natural Earth',
        link: 'https://www.naturalearthdata.com/',
        use: 'Borders, the Mexican states, lakes outside Mexico, roads and railways of the base map, and the choice of rivers, their names and their rank (their courses come from INEGI and NHD).',
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
        use: 'Names and locations of places, summits, passes and springs in New Mexico and Arizona, and the mouth-to-head lines that valley names are set along.',
        licence: 'Public domain',
        credit: 'Place names courtesy of the U.S. Geological Survey (GNIS)',
      },
      {
        name: 'GeoNames',
        link: 'https://www.geonames.org/',
        use: 'Names and locations of places, summits, passes, springs, ranches and stations in Sonora and Chihuahua, and of the ranges and mesas lettered along their axes.',
        licence: 'CC BY 4.0',
        credit: 'GeoNames',
      },
      {
        name: 'GMBA Mountain Inventory v2 (Global Mountain Biodiversity Assessment)',
        link: 'https://www.earthenv.org/mountains',
        use: 'Mountain range outlines in the United States, whose long axes the range names are set along.',
        licence: 'CC BY 4.0',
        credit: 'Snethlage, M.A. et al. (2022), GMBA Mountain Inventory v2, GMBA-EarthEnv',
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
        use: 'Satellite imagery for the Satellite and Compare views and the Satellite tint, and the Topo basemap, on MapTiler’s free plan. The MapTiler logo shows on the map whenever either does.',
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
            <a href={repoUrl('docs/inspiration/rumsey.md')}>list</a> gives each one. Nothing from them is
            reproduced.
          </>
        ),
        licence: 'Links only',
      },
      {
        name: 'Carl Churchill, Variety in hachure',
        link: 'https://churchillgeo.com/variety-in-hachure/',
        use: (
          <>
            A post gathering oblique and block-diagram maps, which set the Oblique view’s style. It follows three of
            them: Tau Rho Alpha’s <cite>Atlas of Oblique Maps</cite> (USGS, 1988) for its long downhill strokes,
            Frank Holmes’s <cite>Estado da Guanabara</cite> (1965) for its stippled lowlands, and Charles Owens’s{' '}
            <cite>The Panama Canal</cite> (1928) for its bold shadows. The{' '}
            <a href={repoUrl('docs/inspiration/churchill.md')}>list</a> links each map. Nothing from them is reproduced.
          </>
        ),
        licence: 'Links only',
      },
      {
        name: 'Monnier and Le Bourguignon-Duperré, Carte générale de la Martinique (1831), David Rumsey Map Collection',
        link: 'https://www.davidrumsey.com/luna/servlet/detail/RUMSEY~8~1~372081~90137794:Carte-Generale-De-La-Martinique',
        use: (
          <>
            A French navy chart that draws what grows on the ground in the same ink as its hachures. The land cover’s
            ink textures follow the kind of mark it uses (<a href={repoUrl('docs/decisions/0042-land-cover-in-ink.md')}>decision 0042</a>).
            Nothing from it is reproduced.
          </>
        ),
        licence: 'Links only',
      },
      {
        name: 'u/lost-my-glasses, Example of Land Cover Hachure Lines (r/mapmaking)',
        link: 'https://www.reddit.com/r/mapmaking/comments/1w1xxt1/example_of_land_cover_hachure_lines/',
        use: (
          <>
            The thread that pointed to the Martinique chart, after u/TheCountVonZeppelin’s{' '}
            <a href="https://www.reddit.com/r/mapmaking/comments/1w1pr3x/an_experiment_in_land_cover_hachures/">An experiment
            in land cover hachures</a>, and the idea of drawing land cover in ink.
          </>
        ),
        licence: 'Links only',
      },
      {
        name: 'Cartographers’ Guild',
        link: repoUrl('docs/inspiration/guild.md'),
        use: 'Tutorials and threads read for the hand-drawn style; the index lists each one. Nothing from them is reproduced.',
        licence: 'Links only',
      },
    ],
  },
]

type Drawing = { id: string; label: string; credit: string; first_seen: string }

// The vignettes' sources, read from data/vignettes.geojson. Only the drawings the reader has reached are listed,
// because a drawing's subject can give the story away.
function useDrawings(reached: string): { shown: Drawing[]; hidden: number } {
  const [all, setAll] = useState<Drawing[]>([])
  useEffect(() => {
    fetch(`${import.meta.env.BASE_URL}data/vignettes.geojson`)
      .then((r) => (r.ok ? r.json() : { features: [] }))
      .then((fc: { features: { properties: Drawing & { kind: string } }[] }) =>
        setAll(fc.features.map((f) => f.properties).filter((p) => p.kind === 'vignette' && p.credit)),
      )
      .catch(() => setAll([]))
  }, [])
  const shown = all.filter((d) => shownAt(d, reached)).sort((a, b) => a.first_seen.localeCompare(b.first_seen))
  return { shown, hidden: all.length - shown.length }
}

// The photos the reader has reached, by place, with their full credit (decision 0067). `photos` has already passed
// the spoiler filter. A context place shows from the start, so it carries no first_seen.
function PhotoCredits({ story, photos, spoilers }: { story: Story | null; photos: PlacePhotos[]; spoilers: boolean }) {
  return (
    <>
      <h2>Photos</h2>
      <p>
        The photos on the cards are from <a href="https://commons.wikimedia.org/">Wikimedia Commons</a>. Each keeps its own licence:
        public domain, CC0, CC BY or CC BY-SA. They are not part of this site’s CC BY licence, and a CC BY-SA photo stays under CC BY-SA.
      </p>
      {photos.length > 0 && (
        <dl className="credits">
          {photos.map((e) => {
            const place = (byId(story, 'places', e.place_id) ?? byId(story, 'stops', e.place_id))?.properties
            const placeSeen = place?.role === 'context' ? undefined : place?.first_seen
            return (
              <div key={e.place_id} data-first-seen={placeSeen}>
                <dt>{place?.name ?? e.place_id}</dt>
                {e.photos.map((p) => (
                  <dd key={p.file} data-first-seen={p.first_seen ?? placeSeen}>
                    <PhotoCredit photo={p} />
                    {p.date && <span className="meta"> Taken {p.date}.</span>}
                  </dd>
                ))}
              </div>
            )
          })}
        </dl>
      )}
      {spoilers && <p className="meta">The credits for photos further on in the book show once you reach them.</p>}
    </>
  )
}

type CreditsProps = { reached: string; spoilers: boolean; story: Story | null; photos: PlacePhotos[] }

export function Credits({ reached, spoilers, story, photos }: CreditsProps) {
  const drawings = useDrawings(reached)
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
                </dd>
              </div>
            ))}
          </dl>
        </section>
      ))}
      <h2>Drawings</h2>
      <p>
        The vignettes are drawn for this site in one pen with the mountain glyphs. Some are traced from public-domain
        photographs; the rest are drawn by hand after references, whose licences allow it.
      </p>
      <dl className="credits">
        {LARGE_ART.map((d) => (
          <div key={d.id}>
            <dt>{d.name} (the opening view)</dt>
            <dd>{d.credit}</dd>
          </div>
        ))}
      </dl>
      {drawings.shown.length > 0 && (
      <dl className="credits">
        {drawings.shown.map((d) => (
          <div key={d.id}>
            <dt>{d.label}</dt>
            <dd>{d.credit}</dd>
          </div>
        ))}
      </dl>
      )}
      {drawings.hidden > 0 && <p className="meta">The credits for drawings further on in the book show once you reach them.</p>}
      <PhotoCredits story={story} photos={photos} spoilers={spoilers} />
      <h2>This site</h2>
      <p>
        The story data, notes and translations written for this site are CC BY 4.0. The code is MIT, except the
        hachure script, which keeps its GPL-3.0 licence. See the <a href="#/data">Data page</a> and the{' '}
        <a href={REPO_URL}>repository</a>.
      </p>
    </>
  )
}
